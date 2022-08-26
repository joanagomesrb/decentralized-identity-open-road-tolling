package com.example.myobu;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;

import org.hyperledger.indy.sdk.IndyException;
import org.hyperledger.indy.sdk.anoncreds.Anoncreds;
import org.hyperledger.indy.sdk.anoncreds.AnoncredsResults;
import org.hyperledger.indy.sdk.crypto.Crypto;
import org.hyperledger.indy.sdk.pool.Pool;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.UnknownHostException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class CredentialThread implements Runnable{

    MyWallet myWallet;
    String myDid, myVerkey;
    private static FirebaseAuth mAuth;
    private FirebaseDatabase db;
    private static DatabaseReference databaseRef;
    private static final String USER = "user";
    Socket socket;
    boolean socket_status = false;
    private BufferedReader input;

    public String username;

    CredentialThread(MyWallet myWallet, String myDid, String myVerkey, String username, int count) {
        System.out.println("credential thread");
        this.myDid = myDid;
        this.myVerkey = myVerkey;
        this.myWallet = myWallet;
        this.username = username;
    }

    @Override
    public void run() {
        // connect to pool
       // Pool poolHandle = this.connectPool();
/*        establishConnection();
        if(socket_status){
            System.out.println("socket connection has been established");
            // start secure communication channel establishment
            sendConnectionRequest();
            System.out.println("Connection request sent!");
            listeningToResponse();
        }
        this.getCredential();*/
    }
    public Pool connectPool(){
        String poolName = "pool";
        String poolConfig = "{\"genesis_txn\": \"/home/vagrant/code/evernym/indy-sdk/cli/docker_pool_transactions_genesis\"}";
        Pool pool = null;
        try {
            Pool.createPoolLedgerConfig(poolName, poolConfig).get();
            pool = Pool.openPoolLedger(poolName, "{}").get();
        } catch (ExecutionException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch (IndyException e) {
            e.printStackTrace();
        }
        return pool;
    }

    private void sendConnectionRequest(){
        OutputStream out = null;
        try {
            DataOutputStream outputStream = new DataOutputStream(this.socket.getOutputStream());
            JSONObject tmp = new JSONObject();
            tmp.put("type", "connectionRequest");

            outputStream.writeUTF(tmp.toString());
            outputStream.flush();

        } catch (IOException | JSONException e) {
            e.printStackTrace();
        }
    }
    private void listeningToResponse() {
        boolean listening = true;
        boolean creatingCredential = true;
        while (creatingCredential) {
            System.out.println("listening");
            int bufferSize = 0;
            try {
                input = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                String tmp = input.readLine();
                //System.out.println("message received length " + tmp.length());
                System.out.println(tmp);
                //System.out.println("read " + tmp);
                //String read_tmp = "";
                /*String[] separated = tmp.split("\\{", 1);
                System.out.println("separated0" + separated[0]);
                System.out.println("separated1" + separated[1]);
                separated[0] = separated[0].trim();
                System.out.println("separated0" + separated[0]);
                int size = Integer.parseInt(separated[0]);*/

                /*while((tmp = input.readLine()) != null){
                    System.out.println("reading from socket...");
                    //bufferSize += tmp.length();

                    read_tmp += tmp;
                    System.out.println("message received length " + read_tmp.length());
                    System.out.println(read_tmp);
                    if(tmp.equals("\n")){
                        System.out.println("did i break?");
                        break;
                    }
                }*/

                if(tmp == null){
                    System.out.println("Finish creation of credential.");
                    //System.out.println("Received null message! Is the connection broken?");
                    listening = false;

                    //this.socket.close();

                    // TODO: handle null message
                }else {
                    JSONObject string_recv = new JSONObject(tmp);
                    String type = (String) string_recv.get("type");
                    String cred_offer = (String) string_recv.get("credoffer");
                    String cred_def = (String) string_recv.get("creddef");
                    System.out.println("Received new message!");
                    if(type.equals("credoffer")) {
                        System.out.println("Hello Back Office's Credential Offer");
                        System.out.println(cred_offer);
                        System.out.println(cred_def);
                        // create link secret
                        String masterSecretNAme = "master_secret";
                        String linkSecret = Anoncreds.proverCreateMasterSecret(this.myWallet.getMyWalletHandle(), masterSecretNAme).get();
                        //String link_secret = completableFuture_linkSecret.get();
                        /*
                        * byte[] decrypted_message_bytes = completableFuture_unpackMessage.get();
                        String decrypted_message = new String(decrypted_message_bytes, StandardCharsets.UTF_8);
                        System.out.println("DECRIPTED conn response: " + decrypted_message);*/

                        // create credential request
                        System.out.println(cred_offer);
                        System.out.println(cred_def);
                        System.out.println(linkSecret);
                        CompletableFuture<AnoncredsResults.ProverCreateCredentialRequestResult> completableFuture_credRequest = Anoncreds.proverCreateCredentialReq(this.myWallet.getMyWalletHandle(), this.myDid, cred_offer, cred_def, masterSecretNAme);
                        AnoncredsResults.ProverCreateCredentialRequestResult credRequestResult = completableFuture_credRequest.get();
                        String credRequest = credRequestResult.getCredentialRequestJson();
                        System.out.println("CRED REQ");
                        //credRequest = "hellooldfriend";
                        this.sendCredRequestToBO(credRequest);
                    }
                }
            } catch (IOException e) {
                e.printStackTrace();
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
        try {
            socket.shutdownInput();
            socket.shutdownOutput();
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    private void sendCredRequestToBO(String credRequest) {
        try {
            DataOutputStream outputStream = new DataOutputStream(this.socket.getOutputStream());
            JSONObject toSend = new JSONObject();
            toSend.put("type", "credreq");
            toSend.put("req", credRequest);

            String msg = toSend.toString();
            System.out.println(msg.length());


            outputStream.writeUTF(msg);
            outputStream.flush();
        } catch (IOException | JSONException e) {
            e.printStackTrace();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }


    public void getCredential() {
        /*ServerSocket serverSocket;
        Socket clientSocket;
        PrintWriter out;
        BufferedReader in;

        // create socket

        //serverSocket = new ServerSocket(5557);
        // my pi = c

        byte[] b = new byte[0];
        try {
            System.out.println(InetAddress.getByName("192.168.12.98"));
        } catch (UnknownHostException e) {
            e.printStackTrace();
        }
        try {
            InetAddress myIP = InetAddress.getByName("192.168.12.98");
            serverSocket = new ServerSocket(5557, 1, myIP);
            serverSocket.setReuseAddress(true);
            clientSocket = serverSocket.accept();
            out = new PrintWriter(clientSocket.getOutputStream(), true);
            in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
            String mesg = in.readLine();
            System.out.println(mesg);

            String inputLine;
            while ((inputLine = in.readLine()) != null) {
                if (".".equals(inputLine)) {
                    out.println("good bye");
                    break;
                }
                out.println(inputLine);
            }
        } catch (IOException e) {
            System.out.println("ERROR getting credential: " + e.getMessage());
            e.printStackTrace();
        }*/
    }

    private void establishConnection(){
        while(!socket_status){
            try {
                // establish connection
                this.socket = new Socket("192.168.12.141", 5557);
                socket_status = true;

            } catch (IOException e) {
                socket_status = false;
                e.printStackTrace();
            }
        }
    }


}


