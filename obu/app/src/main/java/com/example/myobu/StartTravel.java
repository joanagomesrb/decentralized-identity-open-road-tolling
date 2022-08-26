package com.example.myobu;

import androidx.appcompat.app.AppCompatActivity;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

public class StartTravel extends AppCompatActivity {

    NetworkThread networkThread;
    CommunicationThread communicationThread;

    MyWallet myWallet;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_start_travel);

        getSupportActionBar().setTitle("Travel");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);

       // myWallet = (MyWallet) getIntent().getSerializableExtra("MyWallet");


    }

    public void onClick_startTravel2(View view){
        Toast.makeText(getApplicationContext(), "You have started your travel", Toast.LENGTH_SHORT).show();

        /*Context context = getApplicationContext();

        // Connect to WIFI
        if (checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION}, 0x12345);
        }

        networkThread = new NetworkThread(context, myWallet);
        new Thread(networkThread).start();

        //create did/verkey pair
        myWallet.createNewContextKeys();

        // ############################### Communication process // ############################### \\
        communicationThread = new CommunicationThread(myWallet, myWallet.getDid(), myWallet.getVerkey(), username);
        System.out.println("myWallet.getDid()" + myWallet.getDid());
        System.out.println("myWallet.getVerkey()" + myWallet.getVerkey());
        new Thread(communicationThread).start();*/

    }

    public void onClick_stopTravel2(View view){
        Toast.makeText(getApplicationContext(), "You have stoped your travel!", Toast.LENGTH_SHORT).show();

    }

}