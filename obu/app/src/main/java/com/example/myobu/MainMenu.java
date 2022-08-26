package com.example.myobu;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

import android.Manifest;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.system.ErrnoException;
import android.system.Os;
import android.view.MenuItem;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.beardedhen.androidbootstrap.BootstrapButton;
import com.beardedhen.androidbootstrap.TypefaceProvider;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.Query;
import com.google.firebase.database.ValueEventListener;

import org.hyperledger.indy.sdk.LibIndy;

import org.hyperledger.indy.sdk.wallet.Wallet;
import org.iota.jota.IotaAPI;
import org.iota.jota.dto.response.GetNodeInfoResponse;
import org.iota.jota.IotaAPICore;
import org.iota.jota.error.ArgumentException;

import org.w3c.dom.Text;

import java.io.Serializable;
import java.security.PrivilegedAction;
import java.util.HashMap;


public class MainMenu extends AppCompatActivity {

    MyWallet myWallet;
    NetworkThread networkThread;
    CommunicationThread communicationThread;

    boolean created_wallet_identity, created_wallet_iota;

    public static final String SHARED_PREFS = "sharedPrefs";
    public static String BTN_START_TRAVEL = "BTN_START_TRAVEL";
    public static String BTN_CHECK_PAYMENTS = "BTN_CHECK_PAYMENTS";
    public static String BTN_CONFIG = "BTN_CONFIG";

    private boolean btn_start_travel_value;
    private boolean btn_check_payments_value;
    private boolean btn_config_value;

    private BootstrapButton btn_start_travel;
    private BootstrapButton btn_check_payments;
    private BootstrapButton btn_config;

    //SharedPreferences sharedpref;
    private SharedPreferences sharedPref;

    private FirebaseAuth mAuth;
    private FirebaseDatabase db;
    private DatabaseReference databaseRef;
    private static final String USER = "user";
    String username;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TypefaceProvider.registerDefaultIconSets();
        setContentView(R.layout.activity_main_menu);

        getSupportActionBar().setTitle("Menu");
        //getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        Bundle extras = getIntent().getExtras();
        String uid = extras.getString("uid");
        String username = extras.getString("username");



        this.username = extras.getString("username");
        System.out.println("this.username AQUI" + this.username);



        mAuth = FirebaseAuth.getInstance();
        db = FirebaseDatabase.getInstance();
        databaseRef = db.getReference(USER);

        btn_start_travel = (findViewById(R.id.btn_start_travel));
        btn_check_payments = (findViewById(R.id.btn_check_payments));
        btn_config = findViewById(R.id.btn_config);

        loadData();
        updateViews();


        try {
            //Os.setenv("EXTERNAL_STORAGE", path, true);
            Os.setenv("EXTERNAL_STORAGE", getExternalFilesDir(null).getAbsolutePath(), true);
        } catch (ErrnoException e) {
            e.printStackTrace();
        }

        System.loadLibrary("indy");
        LibIndy.init();

    }

    public void disable(BootstrapButton btn, String type) {
        //btn.setBackgroundColor(getResources().getColor(R.color.blue_disable_btn));
        if (type.equals("iota")) {
            btn.setText("Your IOTA wallet is up to date!");
        } else if (type.equals("identity")) {
            btn.setText("Your Identity wallet is up to date!");
        }

        btn.setEnabled(false);
    }

    public void enable(BootstrapButton btn, String type) {
        //btn.setBackgroundColor(getResources().getColor(R.color.blue_enable_btn) );
        if (type.equals("iota")) {
            btn.setText("Update your IOTA wallet!");
        } else if (type.equals("identity")) {
            btn.setText("Update your Identity wallet!");
        }
        Drawable d = getResources().getDrawable(R.drawable.btn_rounded_edge);
        (findViewById(R.id.btn_create_identity_wallet)).setBackground(d);
        btn.setEnabled(true);
    }



    public void onClick_checkPayments(View view) {
        System.out.println("CHECK PAYMENTS");
        saveState();
        System.out.println("1");

        changeToCheckPatyments();
    }

    public void onClick_settings(View view) {
        System.out.println("SETTINGS");
        saveState();
        changeToSettings();
    }

    public void onClick_startTravel(View view) {
        System.out.println("START TRAVEL");
        //Toast.makeText(getApplicationContext(), "START TRAVEL", Toast.LENGTH_LONG).show();
        saveState();
        changeToStartTravel();

    }

    private void changeToCheckPatyments() {
        System.out.println("CHECK PAYMENTS");
        this.setContentView(R.layout.activity_payments);
        getSupportActionBar().setTitle("My Payments");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);

        //HashMap<Integer, Object> payments = communicationThread.paymentsHashmap;

        //TODO: read from db


        String uid = mAuth.getCurrentUser().getUid();
        System.out.println("uid " + uid);

        /*System.out.println("3");

        IotaAPI api = new IotaAPI.Builder()
                .protocol("https")
                .host("nodes.devnet.iota.org")
                .port(443)
                .build();
        System.out.println("4");
        // Call the `getNodeInfo()` method for information about the IOTA node and the Tangle
        GetNodeInfoResponse response = api.getNodeInfo();
        System.out.println(response);
*/

                //FETCH VALUES FROM FIREBASE



    }
    private void changeToSettings() {
        this.setContentView(R.layout.activity_settings);
        getSupportActionBar().setTitle("Settings");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);
    }

    private void changeToStartTravel() {
        this.setContentView(R.layout.activity_start_travel);
        getSupportActionBar().setTitle("Travel");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        (findViewById(R.id.btn_to_start_travel)).setOnClickListener((e)-> {
            Toast.makeText(getApplicationContext(), "You have STARTED your travel", Toast.LENGTH_SHORT).show();

            Context context = getApplicationContext();

            // Connect to WIFI
            if (checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION}, 0x12345);
            }

            //networkThread = new NetworkThread(context, myWallet);
            networkThread = new NetworkThread(context);
            new Thread(networkThread).start();

            //create did/verkey pair
            myWallet.createNewContextKeys();

            // ############################### Communication process // ############################### \\
            /*communicationThread = new CommunicationThread(myWallet, myWallet.getDid(), myWallet.getVerkey(), this.username);
            System.out.println("myWallet.getDid()" + myWallet.getDid());
            System.out.println("myWallet.getVerkey()" + myWallet.getVerkey());
            new Thread(communicationThread).start();*/
        });
    }

    public void onClick_stopTravel2(View view){
        Toast.makeText(getApplicationContext(), "You have STOPED your travel", Toast.LENGTH_LONG).show();
        communicationThread.stop = true;
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

    public void loadData() {
        sharedPref = getSharedPreferences(SHARED_PREFS, MODE_PRIVATE);

        btn_start_travel_value = sharedPref.getBoolean(BTN_START_TRAVEL, true);
        btn_check_payments_value = sharedPref.getBoolean(BTN_CHECK_PAYMENTS, true);
        btn_config_value = sharedPref.getBoolean(BTN_CONFIG, true);

        //myWallet = (Wallet) databaseRef.child(username).child("wallet");
        //Query query = databaseRef.orderByChild(username).orderByChild("wallet");
        //query.addChildEventListener()

        /*System.out.println("username" + username);

        DatabaseReference walletRef = databaseRef.child(USER).child(User.get).child("wallet");
        walletRef.addListenerForSingleValueEvent(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                //String wallet = (String) snapshot.getValue();
                myWallet = (MyWallet) snapshot.getValue();
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {
                System.out.println("walletRef.addListenerForSingleValueEvent:onCancelled");
            }
        });*/


    }

    public void updateViews() {


        btn_start_travel = (findViewById(R.id.btn_start_travel));
        btn_check_payments = (findViewById(R.id.btn_check_payments));
        btn_config = findViewById(R.id.btn_config);

        btn_start_travel.setEnabled(btn_start_travel_value);
        btn_check_payments.setEnabled(btn_check_payments_value);
        btn_config.setEnabled(btn_config_value);

    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch (item.getItemId()) {
            case android.R.id.home:
                this.setContentView(R.layout.activity_main_menu);
                loadData();
                updateViews();
                break;
        }
        return true;
    }

    public void onClick_pay(View view) {
    }
}