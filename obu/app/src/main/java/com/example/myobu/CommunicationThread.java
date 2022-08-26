package com.example.myobu;

import android.os.Handler;
import android.os.Message;

import androidx.arch.core.internal.SafeIterableMap;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;

import org.hyperledger.indy.sdk.IndyException;
import org.hyperledger.indy.sdk.anoncreds.Anoncreds;
import org.hyperledger.indy.sdk.crypto.Crypto;
import org.hyperledger.indy.sdk.ledger.Ledger;
import org.hyperledger.indy.sdk.ledger.LedgerResults;
import org.hyperledger.indy.sdk.pool.Pool;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Random;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

import static java.lang.Boolean.FALSE;
import static java.lang.Boolean.TRUE;


public class CommunicationThread implements Runnable{
    static String shared = "";
    private final Pool poolHandle;

    //private static JSONObject payments;
    private PrintWriter output;
    private BufferedReader input;
    Socket socket;
    boolean socket_status = false;
    String myDid, myVerkey;
    String nonce_client;
    MyWallet myWallet;
    private String did_rsu;
    private String verkey_rsu;
    public boolean passedToll;
    public boolean stop;

    public Payment payment;
    public HashMap<Integer, Object> paymentsHashmap = new HashMap<>();
    public static int count = 0;

    private static FirebaseAuth mAuth;
    private FirebaseDatabase db;
    private static DatabaseReference databaseRef;
    private static final String USER = "user";

    public String username;

    //public Handler mHandler;
    //public static Handler mHandler;


    static ArrayList<Payment> p;
    static boolean last;
    private String proofRequest;

    String obuSchemasForTollApplication;
    String obuCredDefsForTollApplication;
    String obuRevocRefDefsForTollApplication;
    String obuRevocRegsForTollApplication;


    //public JSONObject payments;


    //Network network;

    public CommunicationThread(MyWallet myWallet, String myDid, String myVerkey, String username, int count, Pool poolHandle){
        //HashMap<Integer, Object> paymentsHashmap = new HashMap<>();

        System.out.println("communication thread");
        this.myDid = myDid;
        this.myVerkey = myVerkey;
        this.myWallet = myWallet;
        nonce_client = generateNonce();
        this.poolHandle = poolHandle;
        this.username = username;

        mAuth = FirebaseAuth.getInstance();
        db = FirebaseDatabase.getInstance();
        databaseRef = db.getReference(USER);

        this.count = count;
        System.out.println("THIS IS MY COUNT " + count);

        p = new ArrayList<>();
        last = false;
    }


    public final static Handler mHandler = new Handler() {
        public void handleMessage(Message msg) {
            // Act on the message
            Message rcvMsg = mHandler.obtainMessage();
            System.out.println("Message received");
            System.out.println(rcvMsg);
            String info = rcvMsg.getData().getString("message");
            System.out.println("info");
            System.out.println(info);
            System.out.println("rcvMsg.getData()");
            System.out.println(rcvMsg.getData());
            last = true;
            CommunicationThread.savePayments();
        }
    };


    @Override
    public void run() {
/*
        Looper.prepare();

        mHandler = new Handler() {
            public void handleMessage(Message msg) {
                // Act on the message
                Message rcvMsg = mHandler.obtainMessage();
                System.out.println("Message received");
                if(rcvMsg.toString().equals("stop")){
                    System.out.println("Message received correctly. Stoping thread.");
                    last = true;
                }
            }
        };
        Looper.loop();
*/
        establishConnection();
        if(socket_status){
            System.out.println("socket connection has been established");
            // start secure communication channel establishment
            sendConnectionRequest();
            this.did_rsu = "";
            this.verkey_rsu = "";
            System.out.println("Connection request sent!");
            listeningToResponse();
        }

    }

    private void listeningToResponse() {
        boolean listening = true;
        boolean stop = false;
        while (!passedToll) {
            System.out.println("listening");
            try {
                input = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                String response_string = input.readLine();

                if(response_string == null){
                    System.out.println("Finish one toll connection.");
                    //System.out.println("Received null message! Is the connection broken?");
                    listening = false;

                    this.socket.close();

                    // TODO: handle null message
                }else {
                    JSONObject string_recv = new JSONObject(response_string);
                    System.out.println("Received this message");
                    System.out.println(string_recv);
                    String type = (String) string_recv.get("type");
                    String message = (String) string_recv.get("info");
                    System.out.println("Received new message!");

                    if(type.equals("connectionResponse")) {
                        passedToll = FALSE;
                        System.out.println("Received a connection response!");


                        byte[] message_bytes = message.getBytes();

                        //CryptoResults.AuthDecryptResult res = Crypto.authDecrypt(this.myWallet.getMyWalletHandle(), this.myVerkey, message_bytes).get();
                        CompletableFuture<byte[]> completableFuture_unpackMessage = Crypto.unpackMessage(this.myWallet.getMyWalletHandle(), message_bytes);

                        byte[] decrypted_message_bytes = completableFuture_unpackMessage.get();
                        String decrypted_message = new String(decrypted_message_bytes, StandardCharsets.UTF_8);
                        System.out.println("DECRIPTED conn response: " + decrypted_message);

                        boolean read_success = this.readMessage(decrypted_message);
                        if (read_success) {
                            System.out.println("Read connection response successfully!");
                            this.sendProofRequest();
                        }
                    }else if(type.equals("proofResponse")) {
                        System.out.println("Received a proof response!");

                        byte[] message_bytes = message.getBytes();

                        //CryptoResults.AuthDecryptResult res = Crypto.authDecrypt(this.myWallet.getMyWalletHandle(), this.myVerkey, message_bytes).get();
                        CompletableFuture<byte[]> completableFuture_unpackMessage = Crypto.unpackMessage(this.myWallet.getMyWalletHandle(), message_bytes);

                        byte[] decrypted_message_bytes = completableFuture_unpackMessage.get();
                        String decrypted_message = new String(decrypted_message_bytes, StandardCharsets.UTF_8);
                        System.out.println("DECRYPTED proof response: ");
                        System.out.println(decrypted_message);

                        JSONObject tmp = new JSONObject(decrypted_message);
                        JSONObject tmp2 = new JSONObject((String) tmp.get("message"));
                        JSONArray i = (JSONArray) tmp2.get("identifiers");
                        System.out.println(i.get(0));
                        String a = i.getString(0);
                        JSONObject identfrs = new JSONObject(a);
                        System.out.println(identfrs);

                        //                        JSONObject i2 = new JSONObject((String) i.get(0));
//                        System.out.println(i2);
//                        System.out.println(tmp2.get("identifiers"));



                        boolean proofVerified = this.verifyProof(identfrs);

                        this.send_something();

                    }else if(type.equals("proofRequest")){
                        System.out.println("Received a proof request!");

                        byte[] message_bytes = message.getBytes();

                        //CryptoResults.AuthDecryptResult res = Crypto.authDecrypt(this.myWallet.getMyWalletHandle(), this.myVerkey, message_bytes).get();
                        CompletableFuture<byte[]> completableFuture_unpackMessage = Crypto.unpackMessage(this.myWallet.getMyWalletHandle(), message_bytes);

                        byte[] decrypted_message_bytes = completableFuture_unpackMessage.get();
                        String decrypted_message = new String(decrypted_message_bytes, StandardCharsets.UTF_8);
                        System.out.println("DECRYPTED proof request: " + decrypted_message);

                        //payments.put("proof response", decrypted_message);

                        this.createProofResponse();

                    }else if(type.equals("paymentRequest")){
                        System.out.println("Received a payment request!");

                        byte[] message_bytes = message.getBytes();

                        //CryptoResults.AuthDecryptResult res = Crypto.authDecrypt(this.myWallet.getMyWalletHandle(), this.myVerkey, message_bytes).get();
                        CompletableFuture<byte[]> completableFuture_unpackMessage = Crypto.unpackMessage(this.myWallet.getMyWalletHandle(), message_bytes);

                        byte[] decrypted_message_bytes = completableFuture_unpackMessage.get();
                        String decrypted_message = new String(decrypted_message_bytes, StandardCharsets.UTF_8);
                        System.out.println("DECRYPTED payment request: " + decrypted_message);

                        passedToll = TRUE;

                        JSONObject tmp = new JSONObject(decrypted_message);
                        String payment_string = (String) tmp.get("message");
                        JSONObject payment_message = new JSONObject(payment_string);
                        double amount = Double.parseDouble(payment_message.get("amount").toString());
                        String iotaAddress = (String) payment_message.get("iota_address");
                        String currentTime = (String) payment_message.get("ct");
                        String date_time[] = currentTime.split(" ");
                        String status = "unpaid";

                        addPayment(currentTime, amount, status, iotaAddress);
                        //savePayment(currentTime, amount, status, iotaAddress);
                    }
                }

            } catch (IOException | IndyException e) {
                e.printStackTrace();
            } catch (InterruptedException e) {
                e.printStackTrace();
            } catch (ExecutionException e) {
                e.printStackTrace();
            } catch (JSONException e) {
                e.printStackTrace();
            }
        }
        try {
            socket.shutdownInput();
            socket.shutdownOutput();
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    private boolean verifyProof(JSONObject proofIdentifiers) throws IndyException {

        this.verifierGetEntitiesFromLedger(this.poolHandle, this.myDid, proofIdentifiers, "obu", null);
        //Anoncreds.verifierVerifyProof(this.proofRequest, proof, this.schemas, this.credentialDefinition, this.revocRegDefs, this.revocRegs);
        System.out.println("Verificating...");
        String raw = null;
        String attr1_referent = null;
        try {
            String tmp1 = (String) proofIdentifiers.get("requested_proof");
            JSONObject tmp2 = new JSONObject(tmp1);
            String tmp3 = (String) tmp2.get("revealed_attrs");
            JSONObject tmp4 = new JSONObject((tmp3));
            String tmp5 = (String) tmp4.get("attr2_referent");
            JSONObject tmp6 = new JSONObject((tmp5));
            raw = (String) tmp6.get("raw");


            String tmp9 = (String) tmp4.get("self_attested_attrs");
            JSONObject tmp10 = new JSONObject((tmp9));
            attr1_referent = (String) tmp6.get("attr1_referent");
        } catch (JSONException e) {
            e.printStackTrace();
        }
        assert ("enabled").equals(raw);
        assert ("rsu").equals(attr1_referent);

        CompletableFuture<Boolean> test = Anoncreds.verifierVerifyProof(this.proofRequest.toString(), proofIdentifiers.toString(),
                this.obuSchemasForTollApplication,
                this.obuCredDefsForTollApplication,
                this.obuRevocRefDefsForTollApplication,
                this.obuRevocRegsForTollApplication);
        Boolean testResult = null;
        try {
            testResult = test.get();
        } catch (ExecutionException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        System.out.println("testResult");
        System.out.println(testResult);
        return true;
    }

    private void verifierGetEntitiesFromLedger(Pool poolHandle, String obuDid, JSONObject tollApplicationProofIdentifiers, String obuName, String timestamp ){
//        JSONObject proofIdentifiersJson = null;
//        try {
//            proofIdentifiersJson = new JSONObject(tollApplicationProofIdentifiers);
//        } catch (JSONException e) {
//            e.printStackTrace();
//        }
        for (int i =0; i< tollApplicationProofIdentifiers.length(); i++){
            System.out.println("proofIdentifiersJson");
            System.out.println(tollApplicationProofIdentifiers);
            // get schema from ledger
            Object receivedSchemaId;
            Object receivedSchema;
            try {
                //(receivedSchemaId, receivedSchema)
                this.obuSchemasForTollApplication = this.getSchema(this.poolHandle, this.myDid, (String) tollApplicationProofIdentifiers.get("schema_id"));
            } catch (JSONException e) {
                e.printStackTrace();
            } catch (InterruptedException e) {
                e.printStackTrace();
            } catch (ExecutionException e) {
                e.printStackTrace();
            } catch (IndyException e) {
                e.printStackTrace();
            }
            // get claim definition from ledger
            // (receivedCredDefId, receivedCredDef)
            try {
                this.obuCredDefsForTollApplication = this.getCredDef(this.poolHandle, this.myDid, (String) tollApplicationProofIdentifiers.get("cred_def_id"));
            } catch (IndyException e) {
                e.printStackTrace();
            } catch (JSONException e) {
                e.printStackTrace();
            } catch (InterruptedException e) {
                e.printStackTrace();
            } catch (ExecutionException e) {
                e.printStackTrace();
            }
            try {
                if(tollApplicationProofIdentifiers.get("rev_reg_id") != null){
                    // Get Revocation Registry Definition from Ledger
                    CompletableFuture<String> getRevRegDefRequest = Ledger.buildGetRevocRegDefRequest(obuDid, tollApplicationProofIdentifiers.get("rev_reg_id").toString());
                    // (revRegId, revRegDefjson)
                    String revRegId;
                    String revRegDefjson = null;
                    try {
                        CompletableFuture<LedgerResults.ParseResponseResult> revReg = Ledger.parseGetRevocRegDefResponse(getRevRegDefRequest.get());
                        LedgerResults.ParseResponseResult tmp = revReg.get();
                        revRegId = tmp.getId();
                        revRegDefjson = tmp.getObjectJson();
                    } catch (IndyException e) {
                        e.printStackTrace();
                    } catch (ExecutionException e) {
                        e.printStackTrace();
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                    // Get Revocation Registry from Ledger
                    if(timestamp == null){
                        timestamp = tollApplicationProofIdentifiers.get("timestamp").toString();
                    }
                    CompletableFuture<String> getRevocRegRequest = Ledger.buildGetRevocRegRequest(this.myDid, (String) tollApplicationProofIdentifiers.get("rev_reg_id"), Long.valueOf(timestamp));
                    // (revRegId, revRegJson, timestamp2)
                    CompletableFuture<LedgerResults.ParseRegistryResponseResult> tmp = Ledger.parseGetRevocRegResponse(getRevocRegRequest.get());
                    LedgerResults.ParseRegistryResponseResult prrr = tmp.get();
                    String id = prrr.getId();
                    String rrj = prrr.getObjectJson();
                    JSONObject revRegJson = new JSONObject(rrj);
                    long timestamp2 = prrr.getTimestamp();
                    JSONObject revRegs = new JSONObject();
                    JSONObject tmp99 = new JSONObject();
                    tmp99.put(String.valueOf(timestamp2), revRegJson);
                    revRegs.put(id, tmp.toString());
                    this.obuRevocRegsForTollApplication = revRegs.toString();
                    JSONObject revRegDefs = new JSONObject();
                    revRegDefs.put(id, revRegDefjson);
                    this.obuRevocRefDefsForTollApplication = revRegDefs.toString();
                    //rev_regs[rev_reg_id] = {timestamp2: revRegJson}
                    //rev_reg_defs[rev_reg_id] = json.loads(revoc_reg_def_json);

                    //return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_reg_defs), json.dumps(rev_regs)

                }
            } catch (JSONException e) {
                e.printStackTrace();
            } catch (IndyException e) {
                e.printStackTrace();
            } catch (InterruptedException e) {
                e.printStackTrace();
            } catch (ExecutionException e) {
                e.printStackTrace();
            }
        }
    }

    public String getSchema(Pool poolHandle, String obuDid, String schemaId) throws IndyException, ExecutionException, InterruptedException, JSONException {
        CompletableFuture<String> getSchemaRequest = Ledger.buildGetSchemaRequest(obuDid, schemaId);
        CompletableFuture<LedgerResults.ParseResponseResult> getSchemaResponse = Ledger.parseGetSchemaResponse(getSchemaRequest.get());
        LedgerResults.ParseResponseResult tmp = getSchemaResponse.get();
        String tmp3 = tmp.getObjectJson();
        String id = tmp.getId();
        JSONObject schemas = new JSONObject();
        schemas.put(id, tmp3);
        return schemas.toString();
    }

    public String getCredDef(Pool poolHandle, String obuDid, String credDefId) throws IndyException, ExecutionException, InterruptedException {
        CompletableFuture<String> getCredDefRequest = Ledger.buildGetCredDefRequest(obuDid, credDefId);
        JSONObject credDefs = new JSONObject();
        try {
            CompletableFuture<LedgerResults.ParseResponseResult> getCredDefResponse = Ledger.parseGetCredDefResponse(getCredDefRequest.get());
            LedgerResults.ParseResponseResult tmp = getCredDefResponse.get();
            String id = tmp.getId();
            String tmp2 = tmp.getObjectJson();
            credDefs.put(id, tmp2);
        } catch (ExecutionException e) {
            e.printStackTrace();
        } catch (InterruptedException | JSONException e) {
            e.printStackTrace();
        }
        return credDefs.toString();
    }

    private void addPayment(String timestamp, double amount, String status, String iotaAddress) {
        count++;
        payment = new Payment(count, timestamp, amount, status, iotaAddress);
        p.add(payment);
        System.out.println("count" + count);
        //savePayments();
    }

    private static void savePayments() {
        //count++;
        //payment = new Payment(count, timestamp, amount, status, iotaAddress);

        for(int i = 0; i < p.size(); i++){
            Payment newPayment = p.get(i);
            System.out.println("KEY in savePayment " + databaseRef.child(mAuth.getCurrentUser().getUid()).child("payments").child(String.valueOf(count)).getKey());
            databaseRef.child(mAuth.getCurrentUser().getUid()).child("payments").child(String.valueOf(newPayment.getCount())).setValue(newPayment);

        }


    }

    private void send_something(){
        try {
            DataOutputStream outputStream = new DataOutputStream(this.socket.getOutputStream());

            JSONObject toSend = new JSONObject();
            toSend.put("type", "something");

            outputStream.writeUTF(toSend.toString());
            outputStream.flush();

        } catch (IOException e) {
            e.printStackTrace();
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    private void createProofResponse(){
        JSONObject tmp = new JSONObject();
        int id = 1234;
        int client_class = 2;
        String license_plate = "12AB34";
        try {
            DataOutputStream outputStream = new DataOutputStream(this.socket.getOutputStream());
            tmp.put("client_id", String.valueOf(id));
            tmp.put("client_licensePlate", license_plate);
            tmp.put("client_class", String.valueOf(client_class));
            byte[] encrypted_message = this.encryptMessage(tmp);

            JSONObject toSend = new JSONObject();
            toSend.put("type", "proofResponse");
            String msg = new String(encrypted_message, StandardCharsets.UTF_8);

            toSend.put("info", msg);

            outputStream.writeUTF(toSend.toString());
            outputStream.flush();
        } catch (JSONException e) {
            e.printStackTrace();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    private void createProofRequest(){
        JSONObject tmp = new JSONObject();
        String nonce = generateNonceProofRequest();
        /*CompletableFuture<String> gn = null;
        String nonce = null;
        try {
            gn = Anoncreds.generateNonce();
            nonce = gn.get();
        } catch (IndyException | ExecutionException | InterruptedException e) {
            e.printStackTrace();
        }*/
        try {
            JSONObject pred1_ref_tmp = new JSONObject()
                    .put("name", "id")
                    .put("p_type", ">=")
                    .put("p_value", String.valueOf(1));
            JSONObject pred1_ref = new JSONObject()
                    .put("predicate1_referent", pred1_ref_tmp);
            JSONObject attr1_ref_tmp = new JSONObject()
                    .put("name", "name");
            JSONObject attr1_ref = new JSONObject()
                    .put("attr1_referent", attr1_ref_tmp);
            JSONObject proofReq = new JSONObject()
                    .put("name", "Toll-Application")
                    .put("version", String.valueOf(0.1))
                    .put("nonce", nonce)
                    .put("requested_attributes", attr1_ref)
                    .put("requested_predicates",pred1_ref);


            this.proofRequest = proofReq.toString();
            System.out.println("This is my proof request");
            System.out.println(this.proofRequest);
        } catch (JSONException e) {
            System.out.println("something went wrong in createProofRequest");
        }

    }

    private void sendProofRequest(){
        //OutputStream out = null;
        this.createProofRequest();
        try {
            DataOutputStream outputStream = new DataOutputStream(this.socket.getOutputStream());
            JSONObject tmp = new JSONObject();
            tmp.put("did_client", (this.myDid).toString());
            tmp.put("client_verkey", (this.myVerkey).toString());
            tmp.put("nonce_client", nonce_client);
            tmp.put("proofReq", this.proofRequest);
            System.out.println("this is my proof request message before encrypting");
            System.out.println(tmp.toString());

            byte[] encrypted_message = this.encryptMessage(tmp);



            JSONObject toSend = new JSONObject();
            toSend.put("type", "proofRequest");
            String msg = new String(encrypted_message, StandardCharsets.UTF_8);

            toSend.put("info", msg);

            outputStream.writeUTF(toSend.toString());
            outputStream.flush();
            System.out.println("Sent proof request!");

        } catch (IOException | JSONException e) {
            e.printStackTrace();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private byte[] encryptMessage(JSONObject tmp) throws Exception  {
        String message_to_send = null;
        String toSend =  tmp.toString();
        byte[] byteArr = toSend.getBytes();

        //result = Crypto.authCrypt(this.myWallet.getMyWalletHandle(), this.myVerkey, this.verkey_rsu, byteArr).get();

        JSONArray receivers = new JSONArray(new String[]{this.verkey_rsu});

        byte[] packedMessage = Crypto.packMessage(this.myWallet.getMyWalletHandle(), receivers.toString(), this.myVerkey, byteArr).get();


        return packedMessage;

    }

    private boolean readMessage(String decrypted_message){
        boolean read_success = false;
        JSONObject decrypted_message_json = null;
        try {
            decrypted_message_json = new JSONObject(decrypted_message);

            JSONObject message_json = new JSONObject((String) decrypted_message_json.get("message"));
            //JSONObject message_json = new JSONObject((String) decrypted_message_json.get("info"));
            System.out.println("READ MESSAGE messsage json " + message_json);
            //JSONObject message_info = (JSONObject) message_json.get("info");
            Iterator<String> keys = message_json.keys();
            while(keys.hasNext()) {
                String key = keys.next();
                if(key.equals("did_rsu")) this.did_rsu = (String) message_json.get("did_rsu");
                if(key.equals("verkey_rsu")) this.verkey_rsu = (String) message_json.get("verkey_rsu");
                if(key.equals("nonce_client")) nonce_client = (String) message_json.get("nonce_client");
            }
            read_success = true;
        } catch (JSONException e) {
            e.printStackTrace();
        }
        return read_success;
    }

    private void sendConnectionRequest(){
        OutputStream out = null;
        try {
            DataOutputStream outputStream = new DataOutputStream(this.socket.getOutputStream());
            JSONObject tmp = new JSONObject();
            tmp.put("type", "connectionRequest");
            tmp.put("did_client", (this.myDid).toString());
            tmp.put("client_verkey", (this.myVerkey).toString());
            tmp.put("nonce_client", nonce_client);

            outputStream.writeUTF(tmp.toString());
            outputStream.flush();

        } catch (IOException | JSONException e) {
            e.printStackTrace();
        }
    }

    private void establishConnection(){
        while(!socket_status){
            try {
                // establish connection
//                this.socket = new Socket("192.168.12.1", 5555);
                this.socket = new Socket("192.168.12.115", 5555);
                socket_status = true;

            } catch (IOException e) {
                socket_status = false;
                e.printStackTrace();
            }
        }
    }

    private String generateNonce(){
        // ascii code
        int min = 48;
        int max = 122;
        int length = 100;
        Random random = new Random();
        String nonce_client = random.ints(min, max + 1)
                .filter(i -> (i <= 57 || i >= 65) && (i <= 90 || i >= 97))
                .limit(length)
                .collect(StringBuilder::new, StringBuilder::appendCodePoint, StringBuilder::append)
                .toString();

        return nonce_client;
    }

    private String generateNonceProofRequest(){
        // ascii code
        int min = 48;
        int max = 122;
        int length = 80;
        Random random = new Random();
        String nonce_client = random.ints(min, max + 1)
                .filter(i -> (i <= 57 || i >= 65) && (i <= 90 || i >= 97))
                .limit(length)
                .collect(StringBuilder::new, StringBuilder::appendCodePoint, StringBuilder::append)
                .toString();

        return nonce_client;
    }

    /*public static JSONObject getPayments(){
        return payments;
    }*/

    public boolean getPassedToll(){
        return passedToll;
    }

}
