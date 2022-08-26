package com.example.myobu;

import androidx.appcompat.app.AppCompatActivity;

import android.os.Bundle;
import android.view.View;

import com.beardedhen.androidbootstrap.TypefaceProvider;

public class Settings extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TypefaceProvider.registerDefaultIconSets();
        setContentView(R.layout.activity_settings);
        getSupportActionBar().setTitle("Settings");
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);
    }

    public void onClick_manageIdWallet(){}
    public void onClick_manageIOTAWallet(){}
    public void onClick_accountSettings(){}
    public void onClick_privacyPolicy(){}

    public void onClick_manageIOTAWallet(View view) {
        // not this
    }

    public void onClick_accountSettings(View view) {
        // not this
    }

    public void onClick_manageIdWallet(View view) {
        // not this
    }
}