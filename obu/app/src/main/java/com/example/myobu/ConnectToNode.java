package com.example.myobu;

import android.location.Address;
import android.os.AsyncTask;

import com.example.myobu.ui.login.ToPay;

import org.iota.jota.IotaAPI;
import org.iota.jota.builder.AddressRequest;
import org.iota.jota.dto.response.GetNewAddressResponse;
import org.iota.jota.dto.response.GetNodeInfoResponse;
import org.iota.jota.dto.response.SendTransferResponse;
import org.iota.jota.error.ArgumentException;
import org.iota.jota.model.Input;
import org.iota.jota.model.Transfer;
import org.iota.jota.utils.SeedRandomGenerator;
import org.iota.jota.utils.TrytesConverter;

import java.lang.reflect.Array;
import java.util.ArrayList;
import java.util.List;

public class ConnectToNode extends AsyncTask<List<ToPay>, Void, Void> {

    String protoocol;
    String host;
    int port;
    IotaAPI api;
    @Override
    protected Void doInBackground(List<ToPay>... params) {

        // Mainet: check balance
        /*api = new IotaAPI.Builder().protocol("http").host("193.136.92.128").port(14265).build();

        System.out.println("api " + api);
        GetNodeInfoResponse test = api.getNodeInfo();
        System.out.println("test " + test);

        List<String> addresses = new ArrayList<String>();
        addresses.add("LRAZGXSV9FPCOO9OIUYLRLHBUJSBCCDBZC9UBPNMHQAGGI9BODPVIBMVCIKNCFVWWSALEBQMCFINHIVV9D9LYEQXSA");


        try {
            long balance = api.getBalance(100, addresses.get(0));
            System.out.printf("Your balance is: %s \n", balance);
        } catch (ArgumentException e) {
            // Handle error
            e.printStackTrace();
        }*/

        // DONTDELETE: Mainet - send Hello World
        //api = new IotaAPI.Builder().protocol("http").host("193.136.92.128").port(14265).build();
        IotaAPI api = null;
        boolean connected = false;
        while(!connected){
            try{
                api = new IotaAPI.Builder().protocol("http").host("193.136.92.128").port(14265).build();
                connected = true;
                System.out.println("connected to 193.136.92.128");
            } catch (Exception e) {
                e.printStackTrace();
                try{
                    api = new IotaAPI.Builder().protocol("http").host("2.56.97.215").port(14265).build();
                    connected = true;
                } catch (Exception f) {
                    f.printStackTrace();
                    try{
                        api = new IotaAPI.Builder().protocol("http").host("34.65.221.190").port(14265).build();
                        connected = true;
                    } catch (Exception g) {
                        g.printStackTrace();
                        try{
                            api = new IotaAPI.Builder().protocol("https").host("nodes.thetangle.org").port(443).build();
                            connected = true;
                        } catch (Exception h) {
                            h.printStackTrace();
                        }
                    }
                }

            }
        }
        if(connected) {
            List<ToPay> listOfPayments = params[0];

            for (int i = 0; i < listOfPayments.size(); i++) {
                ToPay newPay = listOfPayments.get(i);
                String addr = newPay.getAddressToPay();
                double a = newPay.getAmountToPay();

                System.out.println("Payment of " + i);
                pay(api, addr, a);
            }
        }else{
            System.out.println("It wasn't possible to connect to IOTA.");
        }

        // not allowed because balance is zero
        /*try {
            SendTransferResponse response = api.sendTransfer(myRandomSeed, securityLevel, depth, minimumWeightMagnitude, transfers, null, null, false, false, null);
            System.out.println(response.getTransactions());
            if(response.getSuccessfully()[0]){
                Boolean arroz[] = response.getSuccessfully();
                System.out.println("length " + arroz.length);
                System.out.println("Successfull");
            }
        } catch (ArgumentException e) {
            // Handle error
            e.printStackTrace();
        }*/


        //DONTDELETE: devnet - send miotas
        /*IotaAPI api = new IotaAPI.Builder()
                .protocol("https")
                .host("nodes.devnet.iota.org")
                .port(443)
                .build();

        GetNodeInfoResponse test = api.getNodeInfo();
        System.out.println("test " + test);
        int depth = 3;
        int minimumWeightMagnitude = 9;
        int securityLevel = 2;
        String mySeed = "JBN9ZRCOH9YRUGSWIQNZWAIFEZUBDUGTFPVRKXWPAUCEQQFS9NHPQLXCKZKRHVCCUZNF9CZZWKXRZVCWQ";
        /*List<String> address = null;
        try {
            GetNewAddressResponse response = api.generateNewAddresses(new AddressRequest.Builder(mySeed, securityLevel).amount(1).checksum(true).build());
            address = response.getAddresses();
            System.out.printf("Your address is %s", address);
            long balance = api.getBalance(100, response.getAddresses().get(0));
            System.out.printf("Your balance is: %s \n", balance);
        } catch (ArgumentException e) {
            // Handle error
            e.printStackTrace();
        }*/
        /*String address = "EOXGK9MWJ9LLYQDDSE9OKLCFHEXTSLGWZOOENAXLZXQI9RVTCAORHRTCE9MXIEOHMECYNIDETFUGPXJRCJDJVFOOGZ";
        int value = 1;
        Transfer Transaction = new Transfer(address, value);
        ArrayList<Transfer> transfers = new ArrayList<Transfer>();
        transfers.add(Transaction);
        try {
            long balance = api.getBalance(100, address);
            System.out.printf("Your balance is: %s \n", balance);
            System.out.printf("Sending 1 i to %s \n", address);
            SendTransferResponse response = api.sendTransfer(mySeed, securityLevel, depth, minimumWeightMagnitude, transfers, null, null, false, false, null);
            System.out.println(response.getTransactions());
            if(response.getSuccessfully()[0]){
                Boolean arroz[] = response.getSuccessfully();
                System.out.println("length " + arroz.length);
                System.out.println("Successfull");
            }
        } catch (ArgumentException e) {
            // Handle error
            e.printStackTrace();
        }*/

        return null;
    }

    private void pay(IotaAPI api, String address, double a) {
        int depth = 3;
        int minimumWeightMagnitude = 14;
        int securityLevel = 2;
        String myRandomSeed = SeedRandomGenerator.generateNewSeed();
        String message = TrytesConverter.asciiToTrytes("Hello world");
        String tag = "HELLOWORLD";
        int value = 0;

        Transfer zeroValueTransaction = new Transfer(address, value, message, tag);
        //Transfer zeroValueTransaction = new Transfer(address, value);
        System.out.printf("Your myRandomSeed is %s \n", myRandomSeed);
        System.out.printf("Your address is %s \n", address);
        System.out.printf("Your value is %s \n", value);
        System.out.printf("Your message is %s \n", message);
        System.out.printf("Your tag is %s \n", tag);
        ArrayList<Transfer> transfers = new ArrayList<Transfer>();
        transfers.add(zeroValueTransaction);
        transfers.add(zeroValueTransaction);
        transfers.add(zeroValueTransaction);
        transfers.add(zeroValueTransaction);
        try {
            System.out.println("Sending transactions...");
            SendTransferResponse response = api.sendTransfer(myRandomSeed, securityLevel, depth, minimumWeightMagnitude, transfers, null, null, false, false, null);
            System.out.println(response.getTransactions());
            if (response.getSuccessfully()[0]) {
                Boolean arroz[] = response.getSuccessfully();
                System.out.println("length " + arroz.length);
                System.out.println("Successfull");
            }
        } catch (ArgumentException e) {
            // Handle error
            e.printStackTrace();
        }
    }
}