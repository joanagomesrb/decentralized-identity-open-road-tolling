package com.example.myobu;

import androidx.appcompat.app.AppCompatActivity;

import android.os.Bundle;
import android.widget.ArrayAdapter;

import org.json.JSONException;
import org.json.JSONObject;

public class PaymentsActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_payments);


        /*JSONObject payments_info = CommunicationThread.getPayments();
        try {
            String len = String.valueOf(payments_info.length()-1);
            String payment_request_nr = "payment_request_" + len;
            String payment_req = (String) payments_info.get(payment_request_nr);
            JSONObject payment_request = new JSONObject(payment_req);
            System.out.println("payment_request " + payment_request);

        } catch (JSONException e) {
            e.printStackTrace();
        }*/

        //ArrayAdapter<String> payments = new ArrayAdapter<>(this, );

    }

}