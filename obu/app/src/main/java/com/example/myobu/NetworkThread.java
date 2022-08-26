package com.example.myobu;import com.sun.jna.Library;


import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.net.ConnectivityManager;
import android.net.DhcpInfo;
import android.net.NetworkInfo;
import android.net.wifi.ScanResult;
import android.net.wifi.WifiConfiguration;
import android.net.wifi.WifiManager;
import android.os.Handler;
import android.os.Looper;
import android.text.format.Formatter;


import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.sun.jna.Library;

import org.hyperledger.indy.sdk.wallet.Wallet;


public class NetworkThread implements Runnable {

    MyWallet myWallet;
    WifiManager wifiManager;
    public Context context;
    private List<ScanResult> results;
    boolean isConnected;
    private String AP_IP;

    //public Handler handler;
    //public Looper looper;

    CommunicationThread communicationThread;

    //public AtomicBoolean conn = new AtomicBoolean(false);


    public NetworkThread(Context context){
        System.out.println("network thread");
        this.context = context;
        //this.myWallet = myWallet;
        //this.handler = handler;
    }

    @Override
    public void run() {
        //this.handler.postDelayed(this, 5000);
        //Looper.prepare();
        //looper = Looper.myLooper();
        //handler = new Handler();
        //Looper.loop();

        try {
            results = scanWifi();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public List scanWifi() throws IOException {
        wifiManager = (WifiManager) context.getSystemService(Context.WIFI_SERVICE);
        if(!wifiManager.isWifiEnabled()){
            wifiManager.setWifiEnabled(true);
        }

        BroadcastReceiver wifiScanReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context c, Intent intent) {
                boolean success = intent.getBooleanExtra(
                        WifiManager.EXTRA_RESULTS_UPDATED, false);
                if (success) {
                    results = scanConnectSuccess();
                } else {
                    results = scanConnectSuccess();
                }
            }
        };

        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(WifiManager.SCAN_RESULTS_AVAILABLE_ACTION);
        context.registerReceiver(wifiScanReceiver, intentFilter);

        return results;
    }

    private List scanConnectSuccess() {
        String networkSSID = null;

        results = wifiManager.getScanResults();
        System.out.println(results);

        if(results.size() != 0) {
            for (ScanResult tmp : results) {
                Pattern pattern = Pattern.compile("^RSU");
                Matcher matcher = pattern.matcher(tmp.SSID);
                if (matcher.find() && tmp.SSID != null && !isConnected) {
                    networkSSID = tmp.SSID;
                    isConnected = tryToConnect(networkSSID);
                }
            }
        }
        return results;
    }


    private boolean tryToConnect(String networkSSID){
        boolean connected = false;
        if(networkSSID != null){
            WifiConfiguration wconfig = new WifiConfiguration();
            wconfig.SSID = "\"" + networkSSID + "\"";
            wconfig.preSharedKey = "\"" + 12345600 + "\"";
            wconfig.status = WifiConfiguration.Status.ENABLED;
            wconfig.allowedGroupCiphers.set(WifiConfiguration.GroupCipher.TKIP);
            wconfig.allowedGroupCiphers.set(WifiConfiguration.GroupCipher.CCMP);
            wconfig.allowedKeyManagement.set(WifiConfiguration.KeyMgmt.WPA_PSK);
            wconfig.allowedPairwiseCiphers.set(WifiConfiguration.PairwiseCipher.TKIP);
            wconfig.allowedPairwiseCiphers.set(WifiConfiguration.PairwiseCipher.CCMP);

            System.out.println("WCONFIG STRING: " + wconfig.toString());

            System.out.println("connecting" + wconfig.SSID + " " + wconfig.preSharedKey);
            wifiManager = (WifiManager) context.getSystemService(Context.WIFI_SERVICE);
            int networkID = wifiManager.addNetwork(wconfig);
            wifiManager.enableNetwork(networkID, true);
            connected = true;
            //conn.set(true);
        }

        if(connected){

            /*
            //create did/verkey pair
            myWallet.createNewContextKeys();

            // ############################### Communication process // ############################### \\
            communicationThread = new CommunicationThread(myWallet, myWallet.getDid(), myWallet.getVerkey());
            System.out.println("myWallet.getDid()" + myWallet.getDid());
            System.out.println("myWallet.getVerkey()" + myWallet.getVerkey());
            new Thread(communicationThread).start();*/


            WifiManager wifiManager = (WifiManager) context.getSystemService(Context.WIFI_SERVICE);
            DhcpInfo dhcpInfo = wifiManager.getDhcpInfo();
            byte[] ipAddress = convert2Bytes(dhcpInfo.serverAddress);
            try {
                AP_IP = InetAddress.getByAddress(ipAddress).getHostAddress();
                System.out.println("RSU network IP " + AP_IP);
            } catch (UnknownHostException e) {
                e.printStackTrace();
            }

            int ip = wifiManager.getConnectionInfo().getIpAddress();
            //int ip = wifiManager.getConnectitvMessagesonInfo().getIpAddress();
            System.out.println("My network IP " + Formatter.formatIpAddress(ip));


            ConnectivityManager cm = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
            NetworkInfo ni = cm.getActiveNetworkInfo();
            System.out.println("Network Info " + ni);
        }
        return connected;
    }

    private static byte[] convert2Bytes(int hostAddress) {
        byte[] addressBytes = { (byte)(0xff & hostAddress),
                (byte)(0xff & (hostAddress >> 8)),
                (byte)(0xff & (hostAddress >> 16)),
                (byte)(0xff & (hostAddress >> 24)) };
        return addressBytes;
    }

    public boolean getIsConnected(){
        return isConnected;
    }

}
