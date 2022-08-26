package com.example.myobu;

import androidx.appcompat.app.AppCompatActivity;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.wifi.ScanResult;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.os.Handler;
import android.system.ErrnoException;
import android.system.Os;
import android.view.View;
import android.widget.Button;

import org.hyperledger.indy.sdk.LibIndy;
import org.hyperledger.indy.sdk.wallet.Wallet;

import com.google.firebase.auth.FirebaseAuth;
import com.sun.jna.Library;


import java.io.File;
import java.io.PrintWriter;
import java.net.Socket;
import java.util.List;

import static java.lang.Boolean.TRUE;

public class MainActivity extends AppCompatActivity {

    private List<ScanResult> results;
    private String AP_IP;
    MyWallet myWallet;
    boolean onTravel = TRUE;
    private volatile boolean stop_travel;

    //private Handler handler = new Handler();
    NetworkThread networkThread;
//    CommunicationThread communicationThread;

    private FirebaseAuth mAuth;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        getSupportActionBar().setTitle("On Board Unit");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);


        disable((Button) findViewById(R.id.btn_stop_travel));
        disable((Button) findViewById(R.id.btn_check_payments));
        disable((Button) findViewById(R.id.btn_start_travel));

        //System.setProperty("jna.library.path", "/home/joana/Downloads/jna-6.1.0");

        /*File dataDir = getApplicationContext().getDataDir();
        System.out.println("datadir=" + dataDir.getAbsolutePath());
        File externalFilesDir = getExternalFilesDir(null);
        String path = externalFilesDir.getAbsolutePath();
        System.out.println("axel externalFilesDir=" + path);
*/
        try {
            //Os.setenv("EXTERNAL_STORAGE", path, true);
            Os.setenv("EXTERNAL_STORAGE", getExternalFilesDir(null).getAbsolutePath(), true);
        } catch (ErrnoException e) {
            e.printStackTrace();
        }

        System.loadLibrary("indy");

       /* File[] files = externalFilesDir.listFiles();
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

        // ############################### Hyperledger Indy // ############################### \\
        LibIndy.init();
       /*MyWallet myWallet = new MyWallet();
        myWallet.createWallet();
        myWallet.createNewContextKeys();

        System.out.println("MY DID: " + myWallet.getDid());*/

        // ############################### Firebase // ############################### \\
        mAuth = FirebaseAuth.getInstance();

    }

    public void disable(Button btn){
        btn.setBackgroundColor(getResources().getColor(R.color.blue_disable_btn));
        btn.setEnabled(false);
    }
    public void enable(Button btn){
        btn.setBackgroundColor(getResources().getColor(R.color.blue_enable_btn) );
        btn.setEnabled(true);
    }

    public void onClick_createWallet(View view){
        myWallet = new MyWallet();
        //myWallet.createWallet(username);

        enable(findViewById(R.id.btn_start_travel));
        disable(findViewById(R.id.btn_create_wallet));
    }

    public void onClick_startTravel(View view) {
        //enable(findViewById(R.id.btn_check_payments));

       // enable(findViewById(R.id.btn_check_payments));
        //enable((Button) findViewById(R.id.btn_check_payments));
        //Button btn = findViewById(R.id.btn_check_payments);
        //btn.setEnabled(true);

        enable(findViewById(R.id.btn_stop_travel));
        if(findViewById((R.id.btn_stop_travel)).isEnabled()){
            System.out.println("BTN stop travel has been enabled!");
        }

        startTravel();
    }

    public void startTravel(){
        //disable(findViewById(R.id.btn_start_travel));

        stop_travel = false;
        //while(!stop_travel) {
        // ############################### Network Service Discovery // ############################### \\
        Context context = getApplicationContext();

        // Connect to WIFI
        if (checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION}, 0x12345);
        }

        networkThread = new NetworkThread(context);
        new Thread(networkThread).start();
        //networkThread.run();

        // ############################### Communication process // ############################### \\
        /*communicationThread = new CommunicationThread(myWallet, myWallet.getDid(), myWallet.getVerkey());
        new Thread(communicationThread).start();*/

    }

    public void onClick_stopTravel(View view){
        stop_travel = true;
        //System.out.println("HELLO STOP BTN");
        //networkThread.looper.quit();
        //handler.removeCallbacks(networkThread);
    }

    public void onClick_getPayments(View view){
        openPaymentsActivity();
    }

    public void openPaymentsActivity(){
        Intent intent = new Intent(this, PaymentsActivity.class);
        startActivity(intent);
    }

}