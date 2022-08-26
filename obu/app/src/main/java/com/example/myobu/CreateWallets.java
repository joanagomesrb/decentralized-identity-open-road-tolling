package com.example.myobu;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.system.ErrnoException;
import android.system.Os;
import android.view.MenuItem;
import android.view.View;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import com.beardedhen.androidbootstrap.BootstrapButton;
import com.beardedhen.androidbootstrap.TypefaceProvider;
import com.example.myobu.ui.login.ToPay;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;

import org.hyperledger.indy.sdk.IndyException;
import org.hyperledger.indy.sdk.LibIndy;
import org.hyperledger.indy.sdk.pool.Pool;
import org.hyperledger.indy.sdk.pool.PoolJSONParameters;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class CreateWallets extends AppCompatActivity implements PaymentsAdapter.CheckboxCheckedListener {

    //private static final String DEFAULT_GENESIS_FILE = ;
    MyWallet myWallet;
    NetworkThread networkThread;
    CommunicationThread communicationThread;

    boolean created_wallet_identity, created_wallet_iota, created_credential;

    public static final String SHARED_PREFS = "sharedPrefs";
    public static String BTN_CREATE_ID_WALLET = "BTN_CREATE_ID_WALLET";
    public static String TXT_BTN_CREATE_ID_WALLET = "TXT_BTN_CREATE_ID_WALLET";
    public static String BTN_CREATE_IOTA_WALLET = "BTN_CREATE_IOTA_WALLET";
    public static String TXT_BTN_CREATE_IOTA_WALLET = "TXT_BTN_CREATE_IOTA_WALLET";
    public static String TXT_IOTA_WARNING = "TXT_IOTA_WARNING";
    public static String TXT_ID_WARNING = "TXT_ID_WARNING";

    public static String BTN_START_TRAVEL = "BTN_START_TRAVEL";
    public static String BTN_CHECK_PAYMENTS = "BTN_CHECK_PAYMENTS";
    public static String BTN_CONFIG = "BTN_CONFIG";

    private boolean btn_start_travel_value;
    private boolean btn_check_payments_value;
    private boolean btn_config_value;

    private BootstrapButton btn_start_travel;
    private BootstrapButton btn_check_payments;
    private BootstrapButton btn_config;

    private boolean btn_create_wallet_id_value;
    private String txt_btn_create_wallet_id_value;
    private String txt_warning_identity_value;
    private boolean btn_create_wallet_iota_value;
    private String txt_btn_create_wallet_iota_value;
    private String txt_warning_iota_value;


    private BootstrapButton btn_create_wallet_id;
    private BootstrapButton btn_create_wallet_iota;
    private BootstrapButton btn_loading;

    //SharedPreferences sharedpref;
    private SharedPreferences sharedPref;

    String uid;
    String username;
    private FirebaseAuth mAuth;
    private FirebaseDatabase db;
    private DatabaseReference databaseRef;
    private static final String USER = "user";

    int countWallet;

    boolean settings_menu = false;

    boolean paymentsUpdate;

    boolean allowed;
    int count;

    String[] countArray;
    String[] dateArray;
    String[] timeArray;
    String[] amountArray;
    String[] statusArray;
    String[] addrArray;

    double totalPayment;
    String addrToPay;

    PaymentsAdapter paymentsAdapter;
    ListView listViewAdapter;

    String userID;

    final ArrayList<String> checkedPayments = new ArrayList<String>();
    private List<ToPay> toPayList = new ArrayList<ToPay>();


    ConnectToNode connectToNode;

    public Handler mHandler;
    private Pool poolHandle;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        //CommunicationThread.shared
        super.onCreate(savedInstanceState);
        TypefaceProvider.registerDefaultIconSets();
        setContentView(R.layout.activity_create_wallets);

        getSupportActionBar().setTitle("Create Wallets");

        Bundle extras = getIntent().getExtras();
        this.uid = extras.getString("uid");
        this.username = extras.getString("username");

        System.out.println(" Create wallets uid " + uid);
        System.out.println("Create wallets  username " + username);

        mHandler = CommunicationThread.mHandler;


        paymentsUpdate = false;

        mAuth = FirebaseAuth.getInstance();
        db = FirebaseDatabase.getInstance();
        databaseRef = db.getReference(USER);

        btn_create_wallet_id = (findViewById(R.id.btn_create_identity_wallet));
        btn_create_wallet_iota = (findViewById(R.id.btn_create_iota_wallet));

        btn_start_travel = (findViewById(R.id.btn_start_travel));
        btn_check_payments = (findViewById(R.id.btn_check_payments));
        btn_config = findViewById(R.id.btn_config);

        //btn_loading = findViewById(R.id.btn_loading);

        try {
            //Os.setenv("EXTERNAL_STORAGE", path, true);
            Os.setenv("EXTERNAL_STORAGE", getExternalFilesDir(null).getAbsolutePath(), true);
        } catch (ErrnoException e) {
            e.printStackTrace();
        }

        System.loadLibrary("indy");
        LibIndy.init();

        //sreadCertificate();

    }

    private void readCertificate() {
        String certificate = null;
        try {
            InputStream in = getApplicationContext().getAssets().open("certificate.txt");
            int size = in.available();
            byte[] buffer = new byte[size];
            in.read(buffer);
            in.close();
            certificate = new String(buffer, "UTF-8");

            JSONObject certJ = new JSONObject(certificate);
            String c_name = (String) certJ.get("name");
            String c_version = (String) certJ.get("version");
            JSONObject certConf = (JSONObject) certJ.get("config");
            String c_rev_support = (String) certConf.get("support_revocation");
            JSONObject certJAtt = (JSONObject) certJ.get("attributes");
            String c_att_id = (String) certJAtt.get("id");
            String c_att_lp = (String) certJAtt.get("license_plate");
            String c_att_class = (String) certJAtt.get("class");
            String c_att_reg_year = (String) certJAtt.get("registration_year");
            String c_att_reg_mont = (String) certJAtt.get("registration_month");

            System.out.println("Certificate has been read successfully!");

        } catch (IOException | JSONException e) {
            e.printStackTrace();
        }
    }

    public void disable(BootstrapButton btn, String type) {
        //btn.setBackgroundColor(getResources().getColor(R.color.blue_disable_btn));
        if (type.equals("iota")) {
            btn.setText("Your IOTA wallet was successfully created");
        } else if (type.equals("identity")) {
            btn.setText("Your Identity was successfully created");
        }
        btn.setEnabled(false);
    }

    public void enable(BootstrapButton btn, String type) {
        //btn.setBackgroundColor(getResources().getColor(R.color.blue_enable_btn) );
        if (type.equals("iota")) {
            btn.setText("Update your IOTA wallet");
        } else if (type.equals("identity")) {
            btn.setText("Update your Identity wallet");
        }
        btn.setEnabled(true);
    }

    public void onClick_createIdentityWallet(View view) {

        myWallet = new MyWallet();
        myWallet.createWallet(uid);
        //TODO: update wallet in databse (in wallet)

        created_wallet_identity = true;

        disable(findViewById(R.id.btn_create_identity_wallet), "identity");

        checkWallets();
    }

    public void onClick_createIOTAWallet(View view) {

        created_wallet_iota = true;

        disable(findViewById(R.id.btn_create_iota_wallet), "iota");

        checkWallets();

    }

    public void checkWallets() {
        if (created_wallet_identity && created_wallet_iota && created_credential) {
            this.setContentView(R.layout.activity_main_menu);
            getSupportActionBar().setDisplayHomeAsUpEnabled(false);
            getSupportActionBar().setTitle("On Board Unit");
            loadData("main_menu");
            updateViews("main_menu");
            saveState();
            //this.setContentView(R.layout.activity_main_menu);
            //getSupportActionBar().setDisplayHomeAsUpEnabled(false);
            //getSupportActionBar().setTitle("On Board Unit");
            //getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        }
    }

    public void onClick_checkPayments(View view) {
        System.out.println("CHECK PAYMENTS");
        saveState();
        changeToCheckPatyments();
    }

    private void changeToCheckPatyments() {
        System.out.println("CHECK PAYMENTS");
        this.setContentView(R.layout.activity_payments);
        getSupportActionBar().setTitle("My Payments");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);

        paymentsUpdate = true;

        String uid = mAuth.getCurrentUser().getUid();

        final ArrayList<Payment> list = new ArrayList<>();

        DatabaseReference dbRef = FirebaseDatabase.getInstance().getReference().child(USER).child(uid).child("payments");
        dbRef.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                list.clear();
                for (DataSnapshot sn : snapshot.getChildren()){
                    HashMap newPayment = (HashMap) sn.getValue();
                    String[] timestamp = ((String) newPayment.get("timestamp")).split(" ");
                    //String txt = (Long) newPayment.get("count") + " " + timestamp[0] + " "  + timestamp[1]  + " "  +  (double) newPayment.get("amount")  + " "  + (String) newPayment.get("status")  + " "  +  (String) newPayment.get("iotaAddress");
                    Payment payment = new Payment(((Long) newPayment.get("count")).intValue(), timestamp[0], timestamp[1], (double) newPayment.get("amount"), (String) newPayment.get("status"), (String) newPayment.get("iotaAddress"));
                    list.add(payment);
                    // TODO: add this to an adaptar, and show it on screen; let the user choose to pay them (which ones?) (or to complain/refuse
                }
                System.out.println("HELLO YOUU");
                if(paymentsUpdate){
                    updateView(list);
                }
            }
            @Override
            public void onCancelled(@NonNull DatabaseError error) {

            }
        });
    }

    private void updateView(ArrayList<Payment> list) {
        //PaymentsAdapter adapter = new PaymentsAdapter(this, R.layout.activity_payments, list);
        countArray = new String[list.size()];
        dateArray = new String[list.size()];
        timeArray = new String[list.size()];
        amountArray = new String[list.size()];
        statusArray = new String[list.size()];
        addrArray = new String[list.size()];

        for(int i = 0; i< list.size(); i++){
            countArray[i] = String.valueOf(list.get(i).getCount());
            dateArray[i] = list.get(i).getData();
            timeArray[i] = list.get(i).getTimestamp();
            amountArray[i] = String.valueOf(list.get(i).getAmount());
            statusArray[i] = list.get(i).getStatus();
            addrArray[i] = list.get(i).getIotaAddress();
        }
        paymentsAdapter = new PaymentsAdapter(this, R.layout.activity_list_view, list, this.uid);
        listViewAdapter = (ListView) findViewById(R.id.listView);
        listViewAdapter.setAdapter(paymentsAdapter);
        paymentsAdapter.setCheckedListener((PaymentsAdapter.CheckboxCheckedListener) this);
    }

    public void getCheckboxCheckedListener(int position, boolean checked) {
        if(checked) {
            System.out.println("this is the amount? " + amountArray[position]);
            checkedPayments.add(countArray[position]);
            double tmp = Double.parseDouble(amountArray[position]);
            //Array[] payments_addrs = new Array[];
            //this.payments_addrs.add(addrArray[position]);
            //this.payments_addrs[addrArray[position]].add(amount);
            //this.addrToPay = addrArray[position];

            this.totalPayment += tmp;
            ToPay newPay = new ToPay(addrArray[position], Double.parseDouble(amountArray[position]));
            this.toPayList.add(newPay);
            System.out.println("this amount payment was added to checked payments list " + amountArray[position]);
        }else{
            for(int i = 0; i<checkedPayments.size(); i++){
                if((checkedPayments.get(i)).equals(countArray[position])){
                    checkedPayments.remove(i);
                    double tmp = Double.parseDouble(amountArray[position]);
                    this.totalPayment -= tmp;
                    System.out.println("this amount payment was retrieved from checked payments list " + amountArray[position]);
                }
            }
        }
        // toPay = count (to db ref), amount (to sum), iotaAddress
    }



    public void onClick_startTravel(View view) {

        saveState();
        changeToStartTravel();

    }

    /*private void changeToCheckPayments() {
        this.setContentView(R.layout.activity_payments);
        getSupportActionBar().setTitle("My Payments");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);

        System.out.println("CHECK PAYMENTS");
        updatePaymentsView();

        //ConnectToNode node = new ConnectToNode();
        //node.execute();
    }*/

    /*private void updatePaymentsView() {

        HashMap<Integer, Object> payments = communicationThread.paymentsHashmap;


        System.out.println(0);
        System.out.println(payments.get(0));
        System.out.println(0);
        System.out.println(payments.get(1));


        String uid = mAuth.getCurrentUser().getUid();
        System.out.println("uid " + uid);

        databaseRef.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                String whateber = snapshot.child(uid).getValue().toString();
                System.out.println(whateber);
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {
                System.out.println("whateber");
            }
        });

    }*/

    public void onClick_settings(View view) {
        System.out.println("SETTINGS");
        saveState();
        changeToSettings();
    }

    private void changeToSettings() {
        this.setContentView(R.layout.activity_settings);
        getSupportActionBar().setTitle("Settings");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);
    }

    public void onClick_manageIOTAWallet(View view){
        this.setContentView(R.layout.manage_iota);
        getSupportActionBar().setTitle("Manage IOTA Wallet");
        settings_menu = true;
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);
    }

    public void onClick_accountSettings(View view){
        this.setContentView(R.layout.account_settings);
        getSupportActionBar().setTitle("Account Settings");
        settings_menu = true;
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);
    }

    public void onClick_manageIdWallet(View view){
        this.setContentView(R.layout.manage_indy);
        getSupportActionBar().setTitle("Manage Identity Wallet");
        settings_menu = true;
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);
    }


    private void changeToStartTravel() {
        this.setContentView(R.layout.activity_start_travel);
        getSupportActionBar().setTitle("Travel");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);

        String uid = mAuth.getCurrentUser().getUid();
        final ArrayList<Object> list = new ArrayList<>();

        DatabaseReference dbRef = FirebaseDatabase.getInstance().getReference().child(USER).child(uid).child("payments");
        dbRef.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                list.clear();
                for (DataSnapshot sn : snapshot.getChildren()) {
                    list.add(sn.getValue().toString());
                    System.out.println(list.size());
                    saveToCount(list);
                }
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {

            }
        });




        (findViewById(R.id.btn_to_start_travel)).setOnClickListener((e)-> {
            Toast.makeText(getApplicationContext(), "You have STARTED your travel", Toast.LENGTH_SHORT).show();

            Context context = getApplicationContext();

            // Connect to WIFI
            if (checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION}, 0x12345);
            }

            networkThread = new NetworkThread(context);
            new Thread(networkThread).start();

            //create did/verkey pair
            System.out.println("myWallet changeToStartTravel LoginAct " + myWallet);
            myWallet.createNewContextKeys();

            // ############################### Communication process // ############################### \\
            communicationThread = new CommunicationThread(myWallet, myWallet.getDid(), myWallet.getVerkey(), this.username, this.count, this.poolHandle);
            System.out.println("myWallet.getDid()" + myWallet.getDid());
            System.out.println("myWallet.getVerkey()" + myWallet.getVerkey());
            new Thread(communicationThread).start();
        });
        //AQUII LETs TRY THIS
        //Intent mainMenuIntent = new Intent(getApplicationContext(), MainMenu.class);

        //mainMenuIntent.putExtra("uid", mAuth.getCurrentUser().getUid());
        //System.out.println("username " + newUser.username);
        /*Bundle bundle = new Bundle();
        bundle.putString("uid", mAuth.getCurrentUser().getUid());
        bundle.putString("username", this.username);
        mainMenuIntent.putExtras(bundle);
        startActivity(mainMenuIntent);*/

        /*this.setContentView(R.layout.activity_start_travel);
        getSupportActionBar().setTitle("Travel");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);

        String uid = mAuth.getCurrentUser().getUid();
        final ArrayList<Object> list = new ArrayList<>();

        DatabaseReference dbRef = FirebaseDatabase.getInstance().getReference().child(USER).child(uid).child("payments");
        dbRef.addValueEventListener(new ValueEventListener() {


            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                list.clear();
                for (DataSnapshot sn : snapshot.getChildren()) {
                    list.add(sn.getValue().toString());
                    saveToCount(list);
                }
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {

            }
        });

        (findViewById(R.id.btn_to_start_travel)).setOnClickListener((e)-> {
            Toast.makeText(getApplicationContext(), "You have STARTED your travel", Toast.LENGTH_SHORT).show();

            Context context = getApplicationContext();

            // Connect to WIFI
            if (checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION}, 0x12345);
            }

            networkThread = new NetworkThread(context);
            new Thread(networkThread).start();

            //create did/verkey pair
            myWallet.createNewContextKeys();

            // ############################### Communication process // ############################### \\
            communicationThread = new CommunicationThread(myWallet, myWallet.getDid(), myWallet.getVerkey(), username, this.countWallet);
            System.out.println("myWallet.getDid()" + myWallet.getDid());
            System.out.println("myWallet.getVerkey()" + myWallet.getVerkey());
            new Thread(communicationThread).start();
        });*/
    }

    private void saveToCount(ArrayList<Object> list) {
        this.count = list.size();
    }

    public void onClick_stopTravel2(View view){

        try{
            communicationThread.stop = true;
            Toast.makeText(getApplicationContext(), "You have STOPED your travel", Toast.LENGTH_LONG).show();
            Message msg = Message.obtain();
            //msg.obj =  "stop"; // Some Arbitrary object
            Bundle b = new Bundle();
            b.putString("message", "stop");
            msg.setData(b);
            System.out.println("Message sent." + msg);
            mHandler.sendMessage(msg);
            System.out.println(msg);
            System.out.println("Message sent.");
        } catch (Exception e) {
            Toast.makeText(getApplicationContext(), "You didn't start a travel yet.", Toast.LENGTH_LONG).show();
            e.printStackTrace();
        }

    }

    public void onClick_pay(View view) {

        // check list of checked payments
        // update in firebase
        // update in app

        Iterator it = paymentsAdapter.userPayments.entrySet().iterator();

        for(int i = 0; i< checkedPayments.size(); i++){
            String pay = checkedPayments.get(i);
            // should each amount/toll have a diferent address to send miotas?
            boolean success = sendMiotas(this.toPayList);
            databaseRef.child(mAuth.getCurrentUser().getUid()).child("payments").child(pay).child("status").setValue("paid");

        }
    }

    public void onClick_clientSelection(View view) {
        System.out.println("Client selected this box " );

    }

    public boolean sendMiotas(List<ToPay> toPayList){
        //connectToNode.sendTransaction(amount, address);
        //connectToNode.sendTransaction(amount);
        connectToNode = (ConnectToNode) new ConnectToNode().execute(toPayList);
        return true;
        //if successful, return true
    }

    public void saveState() {
        System.out.println("SAVING STATE");
        //btn_create_wallet_id_value = btn_create_wallet_id.isEnabled();
        sharedPref = getSharedPreferences(SHARED_PREFS, MODE_PRIVATE);
        SharedPreferences.Editor editor = sharedPref.edit();

        editor.putBoolean(BTN_START_TRAVEL, btn_start_travel.isEnabled());
        editor.putBoolean(BTN_CHECK_PAYMENTS, btn_check_payments.isEnabled());
        editor.putBoolean(BTN_CONFIG, btn_config.isEnabled());


        editor.apply();

    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch (item.getItemId()) {
            case android.R.id.home:
                if(!settings_menu) {
                    this.setContentView(R.layout.activity_main_menu);
                    getSupportActionBar().setDisplayHomeAsUpEnabled(false);
                    getSupportActionBar().setTitle("On Board Unit");
                    loadData("main_menu");
                    updateViews("main_menu");
                    break;
                }else{
                    this.setContentView(R.layout.activity_settings);
                    getSupportActionBar().setDisplayHomeAsUpEnabled(true);
                    getSupportActionBar().setTitle("Settings");
                    loadData("settings_menu");
                    updateViews("settings_menu");
                    settings_menu = false;
                    break;
                }
        }
        return true;
    }

    public void loadData(String type) {
        sharedPref = getSharedPreferences(SHARED_PREFS, MODE_PRIVATE);

        if(type.equals("main_menu")){
            btn_start_travel_value = sharedPref.getBoolean(BTN_START_TRAVEL, true);
            btn_check_payments_value = sharedPref.getBoolean(BTN_CHECK_PAYMENTS, true);
            btn_config_value = sharedPref.getBoolean(BTN_CONFIG, true);
        }else if(type.equals("wallets_menu")) {
            btn_create_wallet_id_value = sharedPref.getBoolean(BTN_CREATE_ID_WALLET, true);
            txt_btn_create_wallet_id_value = sharedPref.getString(TXT_BTN_CREATE_ID_WALLET, "Create your Identity wallet!");

            //btn_loading_value = sharedPref.getBoolean("BTN_LOADING", false);
            //btn_loading.setVisibility(View.GONE);

            btn_create_wallet_iota_value = sharedPref.getBoolean(BTN_CREATE_IOTA_WALLET, true);
            txt_btn_create_wallet_iota_value = sharedPref.getString(TXT_BTN_CREATE_IOTA_WALLET, "Create your IOTA wallet!");
        }else if(type.equals("settings_menu")){

        }
    }

    public void updateViews(String type) {
        if(type.equals("main_menu")){
            btn_start_travel = (findViewById(R.id.btn_start_travel));
            btn_check_payments = (findViewById(R.id.btn_check_payments));
            btn_config = findViewById(R.id.btn_config);

            btn_start_travel.setEnabled(btn_start_travel_value);
            btn_check_payments.setEnabled(btn_check_payments_value);
            btn_config.setEnabled(btn_config_value);
            paymentsUpdate = false;
        }else if(type.equals("wallets_menu")) {
            btn_create_wallet_id = findViewById(R.id.btn_create_identity_wallet);
            btn_create_wallet_iota = (findViewById(R.id.btn_create_iota_wallet));

            // btn_loading = findViewById(R.id.btn_loading);
            //btn_loading.setVisibility(View.GONE);

            btn_create_wallet_id.setEnabled(btn_create_wallet_id_value);
            btn_create_wallet_id.setText(txt_btn_create_wallet_id_value);

            btn_create_wallet_iota.setEnabled(btn_create_wallet_iota_value);
            btn_create_wallet_iota.setText(txt_btn_create_wallet_iota_value);

        }else if(type.equals("settings_menu")){

        }
    }

    public void onClick_createCredential(View view) {
        disable(findViewById(R.id.btn_create_credential), "credential");
        this.created_credential = true;
        /*myWallet.createNewContextKeys();
        System.out.println("myWallet.getDid()" + myWallet.getDid());
        System.out.println("myWallet.getVerkey()" + myWallet.getVerkey());*/
        this.createPool();
        checkWallets();
        //CredentialThread credentialThread = new CredentialThread(myWallet, myWallet.getDid(), myWallet.getVerkey(), this.username, this.count);
        //new Thread(credentialThread).start();
        
    }
    public void createPool(){
        this.setEnvironmentAndLoadLibindyAndroid();
        this.writeDefaultGenesisTransactions("192.168.12.141");
        this.createDefaultPool();
        this.openDefaultPool();

        /*String poolName = "pool";
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
        this.poolHandle = pool;
        System.out.println("THIS IS MY POOL HANDLE");
        System.out.println(this.poolHandle);*/
    }

    private void setEnvironmentAndLoadLibindyAndroid()  {
        String environmentPath = getExternalFilesDir(null).getAbsolutePath();
        try {
            Os.setenv("EXTERNAL_STORAGE", environmentPath, true);
            String indyClientPath = environmentPath + "/" + ".indy_client";
            System.out.println("idyClientPath");
            System.out.println(indyClientPath);
            File file = new
                    File(indyClientPath);
            if (!file.exists()) {
                file.mkdir();
            }
            System.loadLibrary("indy");
            System.out.println("Loaded indy library");
        } catch (ErrnoException e) {
            System.out.println("Could not load indy library");
            //throw new IndyFacadeException("could not set android environment", e);
        }

    }

    public void writeDefaultGenesisTransactions(String poolIPAddress)  {
        String[] genesisTransactions = getDefaultGenesisTxn(poolIPAddress);
        String DEFAULT_GENESIS_FILE = "docker_pool_transactions_genesis.txn";
        writeGenesisTransactions(genesisTransactions, DEFAULT_GENESIS_FILE);
    }



    public void writeGenesisTransactions(String[] genesisContent, String genesisFileName) {
        String environmentPath = getExternalFilesDir(null).getAbsolutePath();
        String indyClientPath = environmentPath + "/" + ".indy_client";
        try {
            File genesisFile = new File(indyClientPath + "/" + genesisFileName);
            FileWriter fw = new FileWriter(genesisFile);
            for (String s : genesisContent) {
                fw.write(s);
                fw.write("\n");
            }
            fw.flush();
            fw.close();
            System.out.println("Wrote default genesis transactions");
        } catch (IOException e) {
            System.out.println("Could not write default genesis transactions");
            //throw new IndyFacadeException("could not write default genesis transactions", e);
        }
    }


    private String[] getDefaultGenesisTxn(String poolIPAddress) {
        String[] s = new String[]{String.format(
                "{\"reqSignature\":{},\"txn\":{\"data\":{\"data\":{\"alias\":\"Node1\",\"blskey\":\"4N8aUNHSgjQVgkpm8nhNEfDf6txHznoYREg9kirmJrkivgL4oSEimFF6nsQ6M41QvhM2Z33nves5vfSn9n1UwNFJBYtWVnHYMATn76vLuL3zU88KyeAYcHfsih3He6UHcXDxcaecHVz6jhCYz1P2UZn2bDVruL5wXpehgBfBaLKm3Ba\",\"blskey_pop\":\"RahHYiCvoNCtPTrVtP7nMC5eTYrsUA8WjXbdhNc8debh1agE9bGiJxWBXYNFbnJXoXhWFMvyqhqhRoq737YQemH5ik9oL7R4NTTCz2LEZhkgLJzB3QRQqJyBNyv7acbdHrAT8nQ9UkLbaVL9NBpnWXBTw4LEMePaSHEw66RzPNdAX1\",\"client_ip\":\"%s\",\"client_port\":9702,\"node_ip\":\"%s\",\"node_port\":9701,\"services\":[\"VALIDATOR\"]},\"dest\":\"Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv\"},\"metadata\":{\"from\":\"Th7MpTaRZVRYnPiabds81Y\"},\"type\":\"0\"},\"txnMetadata\":{\"seqNo\":1,\"txnId\":\"fea82e10e894419fe2bea7d96296a6d46f50f93f9eeda954ec461b2ed2950b62\"},\"ver\":\"1\"}",
                poolIPAddress, poolIPAddress),
                String.format(
                        "{\"reqSignature\":{},\"txn\":{\"data\":{\"data\":{\"alias\":\"Node2\",\"blskey\":\"37rAPpXVoxzKhz7d9gkUe52XuXryuLXoM6P6LbWDB7LSbG62Lsb33sfG7zqS8TK1MXwuCHj1FKNzVpsnafmqLG1vXN88rt38mNFs9TENzm4QHdBzsvCuoBnPH7rpYYDo9DZNJePaDvRvqJKByCabubJz3XXKbEeshzpz4Ma5QYpJqjk\",\"blskey_pop\":\"Qr658mWZ2YC8JXGXwMDQTzuZCWF7NK9EwxphGmcBvCh6ybUuLxbG65nsX4JvD4SPNtkJ2w9ug1yLTj6fgmuDg41TgECXjLCij3RMsV8CwewBVgVN67wsA45DFWvqvLtu4rjNnE9JbdFTc1Z4WCPA3Xan44K1HoHAq9EVeaRYs8zoF5\",\"client_ip\":\"%s\",\"client_port\":9704,\"node_ip\":\"%s\",\"node_port\":9703,\"services\":[\"VALIDATOR\"]},\"dest\":\"8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb\"},\"metadata\":{\"from\":\"EbP4aYNeTHL6q385GuVpRV\"},\"type\":\"0\"},\"txnMetadata\":{\"seqNo\":2,\"txnId\":\"1ac8aece2a18ced660fef8694b61aac3af08ba875ce3026a160acbc3a3af35fc\"},\"ver\":\"1\"}\n",
                        poolIPAddress, poolIPAddress),
                String.format(
                        "{\"reqSignature\":{},\"txn\":{\"data\":{\"data\":{\"alias\":\"Node3\",\"blskey\":\"3WFpdbg7C5cnLYZwFZevJqhubkFALBfCBBok15GdrKMUhUjGsk3jV6QKj6MZgEubF7oqCafxNdkm7eswgA4sdKTRc82tLGzZBd6vNqU8dupzup6uYUf32KTHTPQbuUM8Yk4QFXjEf2Usu2TJcNkdgpyeUSX42u5LqdDDpNSWUK5deC5\",\"blskey_pop\":\"QwDeb2CkNSx6r8QC8vGQK3GRv7Yndn84TGNijX8YXHPiagXajyfTjoR87rXUu4G4QLk2cF8NNyqWiYMus1623dELWwx57rLCFqGh7N4ZRbGDRP4fnVcaKg1BcUxQ866Ven4gw8y4N56S5HzxXNBZtLYmhGHvDtk6PFkFwCvxYrNYjh\",\"client_ip\":\"%s\",\"client_port\":9706,\"node_ip\":\"%s\",\"node_port\":9705,\"services\":[\"VALIDATOR\"]},\"dest\":\"DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya\"},\"metadata\":{\"from\":\"4cU41vWW82ArfxJxHkzXPG\"},\"type\":\"0\"},\"txnMetadata\":{\"seqNo\":3,\"txnId\":\"7e9f355dffa78ed24668f0e0e369fd8c224076571c51e2ea8be5f26479edebe4\"},\"ver\":\"1\"}\n",
                        poolIPAddress, poolIPAddress),
                String.format(
                        "{\"reqSignature\":{},\"txn\":{\"data\":{\"data\":{\"alias\":\"Node4\",\"blskey\":\"2zN3bHM1m4rLz54MJHYSwvqzPchYp8jkHswveCLAEJVcX6Mm1wHQD1SkPYMzUDTZvWvhuE6VNAkK3KxVeEmsanSmvjVkReDeBEMxeDaayjcZjFGPydyey1qxBHmTvAnBKoPydvuTAqx5f7YNNRAdeLmUi99gERUU7TD8KfAa6MpQ9bw\",\"blskey_pop\":\"RPLagxaR5xdimFzwmzYnz4ZhWtYQEj8iR5ZU53T2gitPCyCHQneUn2Huc4oeLd2B2HzkGnjAff4hWTJT6C7qHYB1Mv2wU5iHHGFWkhnTX9WsEAbunJCV2qcaXScKj4tTfvdDKfLiVuU2av6hbsMztirRze7LvYBkRHV3tGwyCptsrP\",\"client_ip\":\"%s\",\"client_port\":9708,\"node_ip\":\"%s\",\"node_port\":9707,\"services\":[\"VALIDATOR\"]},\"dest\":\"4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA\"},\"metadata\":{\"from\":\"TWwCRQRZ2ZHMJFn9TzLp7W\"},\"type\":\"0\"},\"txnMetadata\":{\"seqNo\":4,\"txnId\":\"aa5e817d7cc626170eca175822029339a444eb0ee8f0bd20d3b0b76e566fb008\"},\"ver\":\"1\"}",
                        poolIPAddress, poolIPAddress)};
        return s;
    }

    public void createDefaultPool()  {
        createPool("pool2", "docker_pool_transactions_genesis.txn");

    }

    public void createPool(String poolName, String genesisTransactionsFileName)  {
        String environmentPath = getExternalFilesDir(null).getAbsolutePath();
        String indyClientPath = environmentPath + "/" + ".indy_client";
        try {
            PoolJSONParameters.CreatePoolLedgerConfigJSONParameter createPoolLedgerConfigJSONParameter = new PoolJSONParameters.CreatePoolLedgerConfigJSONParameter(
                    indyClientPath + "/" + genesisTransactionsFileName);
            System.out.println(createPoolLedgerConfigJSONParameter);
            CompletableFuture<Void> test = Pool.createPoolLedgerConfig(poolName, createPoolLedgerConfigJSONParameter.toJson());
            //CompletableFuture<Void> test = Pool.createPoolLedgerConfig(poolName, null);
            Object test2 = test.get();
            System.out.println("created pool config");
        } catch (InterruptedException | ExecutionException | IndyException e) {
            System.out.println("failed to create pool config");
            //throw new IndyFacadeException("could not create pool", e);
        }
    }
    public void openDefaultPool() {
        try {
            Pool.setProtocolVersion(2);
            CompletableFuture<Pool> pH = Pool.openPoolLedger("pool2", null);
            this.poolHandle = pH.get();
            System.out.print("Opened pool");
            System.out.print(this.poolHandle.toString());
        } catch (IndyException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch (ExecutionException e) {
            e.printStackTrace();
        }
    }
}