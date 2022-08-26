package com.example.myobu.ui.login;

import android.Manifest;

import androidx.annotation.NonNull;


import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;

import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import android.os.Handler;
import android.os.Message;
import android.system.ErrnoException;
import android.system.Os;
import android.text.TextUtils;
import android.util.Log;
import android.view.MenuItem;
import android.view.View;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import com.beardedhen.androidbootstrap.BootstrapButton;
import com.example.myobu.CommunicationThread;
import com.example.myobu.ConnectToNode;
import com.example.myobu.CreateAccount;
import com.example.myobu.MyWallet;
import com.example.myobu.NetworkThread;
import com.example.myobu.Payment;
import com.example.myobu.PaymentsAdapter;
import com.example.myobu.R;
import com.example.myobu.User;
import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.Task;
import com.google.firebase.auth.AuthResult;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;

import org.hyperledger.indy.sdk.LibIndy;
import org.hyperledger.indy.sdk.non_secrets.WalletRecord;
import org.hyperledger.indy.sdk.pool.Pool;
import org.hyperledger.indy.sdk.wallet.Wallet;
import org.iota.jota.IotaAPI;
import org.iota.jota.dto.response.GetNodeInfoResponse;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Array;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

public class LoginActivity extends AppCompatActivity implements PaymentsAdapter.CheckboxCheckedListener {

    private LoginViewModel loginViewModel;

    private FirebaseAuth mAuth;
    private FirebaseDatabase db;
    private DatabaseReference database;
    private static final String USER = "user";
    private static final String TAG = "LOGIN";

    FirebaseDatabase rootNode;
    DatabaseReference reference;

    EditText usernameEditText;
    EditText emailEditText;
    EditText passwordEditText;

    User user;
    String userID;

    final ArrayList<String> checkedPayments = new ArrayList<String>();

    public static final String SHARED_PREFS = "sharedPrefs";
    private SharedPreferences sharedPref;
    public static String BTN_START_TRAVEL = "BTN_START_TRAVEL";
    public static String BTN_CHECK_PAYMENTS = "BTN_CHECK_PAYMENTS";
    public static String BTN_CONFIG = "BTN_CONFIG";

    private boolean btn_start_travel_value;
    private boolean btn_check_payments_value;
    private boolean btn_config_value;

    private BootstrapButton btn_start_travel;
    private BootstrapButton btn_check_payments;
    private BootstrapButton btn_config;

    Payment payment;
    PaymentsAdapter paymentsAdapter;
    ListView listViewAdapter;
    CommunicationThread communicationThread;
    NetworkThread networkThread;
    MyWallet myWallet;
    Wallet m;

    FirebaseUser fbUser;
    String username;

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

    private List<ToPay> toPayList = new ArrayList<ToPay>();

    boolean paymentsUpdate;


    ConnectToNode connectToNode;

    boolean settings_menu = false;

    public Handler mHandler;




    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_login);

        getSupportActionBar().setTitle("Login");

        mHandler = CommunicationThread.mHandler;

        //connectToNode = new ConnectToNode("http", "193.136.92.128", 14265);

        this.totalPayment = 0.0;
        paymentsUpdate = false;

        mAuth = FirebaseAuth.getInstance();
        db = FirebaseDatabase.getInstance();
        database = db.getReference(USER);

        emailEditText = findViewById(R.id.email);
        passwordEditText = findViewById(R.id.password);
        final BootstrapButton loginButton = findViewById(R.id.login);

        btn_start_travel = (findViewById(R.id.btn_start_travel));
        btn_check_payments = (findViewById(R.id.btn_check_payments));
        btn_config = findViewById(R.id.btn_config);

        allowed = true;

        loginButton.setEnabled(true);

        loginButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                //String email = "jober3@ua.pt";//emailEditText.getText().toString();
                //String password = "jober3123"; //passwordEditText.getText().toString();
                String email = emailEditText.getText().toString();
                String password = passwordEditText.getText().toString();
                if (TextUtils.isEmpty(email) || TextUtils.isEmpty(password)) {
                    Toast.makeText(getApplicationContext(), "Enter email and password", Toast.LENGTH_LONG).show();
                    return;
                }
                signIn(email, password);
            }

        });



    }

    public boolean sendMiotas(List<ToPay> toPayList){
        //connectToNode.sendTransaction(amount, address);
        //connectToNode.sendTransaction(amount);
        connectToNode = (ConnectToNode) new ConnectToNode().execute(toPayList);
        return true;
        //if successful, return true
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
            database.child(mAuth.getCurrentUser().getUid()).child("payments").child(pay).child("status").setValue("paid");

        }
    }



    public void onClick_clientSelection(View view) {

        //boolean newState = !list.get(position).isChecked();

        System.out.println("Client selected this box " );

        /*int boxID = view.getId();
        System.out.println("ClientSelection box ID "  + boxID);
        View something = view.findViewById(R.id.checkbox_text);

        int x = 123;
        int paymentID = (int) paymentsAdapter.userPayments.get(boxID);
        if(!checkedPayments.contains(paymentID)){
            checkedPayments.add(paymentID);
            System.out.println("This is my payment id in ClientSelection" + paymentID);

        }*/
        //CheckBox checkBox = findViewById(boxID);
        //checkBox.isChecked();//checkBox.setChecked(false);
    }



    public void signIn(String email, String password){
        mAuth.signInWithEmailAndPassword(email, password)
                .addOnCompleteListener(this, new OnCompleteListener<AuthResult>() {
                    @Override
                    public void onComplete(@NonNull Task<AuthResult> task) {
                        if (task.isSuccessful()) {
                            // Sign in success, update UI with the signed-in user's information
                            Log.d(TAG, "signInWithEmail:success");
                            //FirebaseUser user = mAuth.getCurrentUser();
                            //System.out.println("get cuurent user getEmail" + user.getEmail());
                            fbUser = task.getResult().getUser();
                            //System.out.println(fbUser.getEmail());
                            userID = fbUser.getUid();
                            System.out.println("DOIS" + userID);
                            //System.out.println(database.child(USER).child(uid).child("wallet"));
                            updateUI(fbUser);
                        } else {
                            // If sign in fails, display a message to the user.
                            Log.w(TAG, "signInWithEmail:failure", task.getException());
                            Toast.makeText(getApplicationContext(), "Authentication failed.",
                                    Toast.LENGTH_SHORT).show();
                        }

                        // ...
                    }
                });
    }

    private void updateUI(FirebaseUser user) {

        /*File dataDir = getApplicationContext().getDataDir();
        System.out.println("datadir=" + dataDir.getAbsolutePath());
        File externalFilesDir = getExternalFilesDir(null);
        String path = externalFilesDir.getAbsolutePath();
        System.out.println("axel externalFilesDir=" + path);*/

        readCertificate();

        try {
            //Os.setenv("EXTERNAL_STORAGE", path, true);
            Os.setenv("EXTERNAL_STORAGE", getExternalFilesDir(null).getAbsolutePath(), true);
        } catch (ErrnoException e) {
            e.printStackTrace();
        }

        System.loadLibrary("indy");
        LibIndy.init();

        // TODO: check the importance of this
        /*File[] files = externalFilesDir.listFiles();
        System.out.println("axel files :" + files);
        for (int i = 0; i < files.length; ++i) {
            File file = files[i];
            if (file.isDirectory()) {
                System.out.println("axel directory:" + file.getName());
                if (".indy_client".equals(file.getName())) {
                    String[] children = file.list();
                    for (int j = 0; j < children.length; j++)
                    {
                        System.out.println("axel deleting:" + children[j]);
                        new File(file, children[j]).delete();
                    }
                }
            } else {
                System.out.println("axel file     :" + file.getName());
            }
        }*/


        final ArrayList<Object> list = new ArrayList<>();

        DatabaseReference dbRef = FirebaseDatabase.getInstance().getReference().child(USER).child(user.getUid());
        dbRef.addValueEventListener(new ValueEventListener() {
            private String tmpUsername;


            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                list.clear();
                System.out.println("Step1");
                for (DataSnapshot sn : snapshot.getChildren()){
                    //User newUser = sn.getValue(User.class);
                    System.out.println("Step2");

                    String whatever = sn.getValue().toString();
                    System.out.println("whatever" + whatever);
                    list.add(sn.getValue().toString());
                    //System.out.println("lilst " + sn.getValue().toString());
                }
                System.out.println("lilst " + list);
                tmpUsername = (String) list.get(1);
                System.out.println("this.username list before  " + tmpUsername);

                String wh = (String) list.get(list.size()-1);
                String[] tmp1 = wh.split("=");
                System.out.println(tmp1[1]);
                String tmp2 = tmp1[1].replace("}", "");
                int walletHandle = Integer.parseInt(tmp2);
                System.out.println(walletHandle);
                //myWallet = new MyWallet(walletHandle, user.getUid());
                if(allowed) {
                    System.out.println("allowed " + allowed);
                    updateWallet(walletHandle, user.getUid());
                    //savePaymentsCount();
                }
                saveUsername(tmpUsername);
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {

            }
        });

        System.out.println("this.username list after " + this.username);


        this.setContentView(R.layout.activity_main_menu);
        getSupportActionBar().setDisplayHomeAsUpEnabled(false);
        getSupportActionBar().setTitle("On Board Unit");
        loadData("main_menu");
        updateViews("main_menu");


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

    private void updateWallet(int walletHandle, String uid) {
        System.out.println("updateWallet");
        allowed = false;
        myWallet = new MyWallet(walletHandle, uid);
    }

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
        paymentsAdapter = new PaymentsAdapter(this, R.layout.activity_list_view, list, userID);
        listViewAdapter = (ListView) findViewById(R.id.listView);
        listViewAdapter.setAdapter(paymentsAdapter);
        paymentsAdapter.setCheckedListener(this);
    }

    @Override
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

    private void saveUsername(String tmpUsername) {
        this.username = tmpUsername;
    }

    public void loadData(String type) {
        sharedPref = getSharedPreferences(SHARED_PREFS, MODE_PRIVATE);

        if(type.equals("main_menu")){
            btn_start_travel_value = sharedPref.getBoolean(BTN_START_TRAVEL, true);
            btn_check_payments_value = sharedPref.getBoolean(BTN_CHECK_PAYMENTS, true);
            btn_config_value = sharedPref.getBoolean(BTN_CONFIG, true);

        }else if(type.equals("wallets_menu")) {

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

        }else if(type.equals("settings_menu")){

        }
    }

    public void onClick_createAccount(View view) {
        //create new activity
        Intent intent = new Intent(this, CreateAccount.class);
        startActivity(intent);
    }

    public void onClick_startTravel(View view) {
        System.out.println("START TRAVEL");
        //Toast.makeText(getApplicationContext(), "START TRAVEL", Toast.LENGTH_LONG).show();
        saveState();
        changeToStartTravel();

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

            Pool poolHandle = null;
            // ############################### Communication process // ############################### \\
            communicationThread = new CommunicationThread(myWallet, myWallet.getDid(), myWallet.getVerkey(), this.username, this.count, poolHandle);
            System.out.println("myWallet.getDid()" + myWallet.getDid());
            System.out.println("myWallet.getVerkey()" + myWallet.getVerkey());
            new Thread(communicationThread).start();
        });
    }

    private void saveToCount(ArrayList<Object> list) {
        this.count = list.size();
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


}

