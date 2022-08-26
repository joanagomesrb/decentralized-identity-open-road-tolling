package com.example.myobu;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;

import org.hyperledger.indy.sdk.IndyException;
import org.hyperledger.indy.sdk.did.Did;
import org.hyperledger.indy.sdk.did.DidResults;
import org.hyperledger.indy.sdk.wallet.Wallet;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.ObjectOutputStream;
import java.io.PrintWriter;
import java.io.Serializable;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.ExecutionException;

public class MyWallet {

    Wallet walletHandle;
    private String myDid;
    private String verkey;

    private FirebaseAuth mAuth;
    private FirebaseDatabase db;
    private DatabaseReference databaseRef;
    private static final String USER = "user";

    public MyWallet(){
        this.mAuth = FirebaseAuth.getInstance();
        this.db = FirebaseDatabase.getInstance();
        this.databaseRef = db.getReference(USER);
    }

    public MyWallet(int w, String uid) {

        System.out.println("MyWallet walletHAndle" + this.walletHandle);

        final String WALLETName = "MyWallet";
        final String WALLETType = "default";
        String WALLET_CONFIG = null;
        String WALLET_CREDENTIALS = null;
        try {
            WALLET_CONFIG =
                    new JSONObject()
                            .put("id", WALLETName)
                            .put("storage_type", WALLETType)
                            .toString();

            //for wallet encryption + change of key
            WALLET_CREDENTIALS =
                    new JSONObject()
                            .put("key", "key")
                            .toString();
            try {
                Wallet.createWallet(WALLET_CONFIG, WALLET_CREDENTIALS).get();
            } catch (ExecutionException e) {
                System.out.println(e.getMessage());
                if (e.getMessage().indexOf("WalletExistsException") >= 0) {
                    // ignore
                } else {
                    throw new RuntimeException(e);
                }
            }
            try{
                this.walletHandle = Wallet.openWallet(WALLET_CONFIG, WALLET_CREDENTIALS).get();
            } catch (ExecutionException e) {
                System.out.println("MyWallet(int w, String uid) this.walletHandle before" + this.walletHandle);
            }
            System.out.println("MyWallet(int w, String uid) this.walletHandle before" + this.walletHandle);
        } catch (IndyException e) {
            e.printStackTrace();
        } catch (JSONException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        System.out.println("MyWallet(int w, String uid) this.walletHandle after" + this.walletHandle);

        //createWallet(uid);
        /*final String WALLETName = "MyWallet";
        final String WALLETType = "default";
        String WALLET_CONFIG = null;
        String WALLET_CREDENTIALS = null;
        try {
            WALLET_CONFIG =
                    new JSONObject()
                            .put("id", WALLETName)
                            .put("storage_type", WALLETType)
                            .toString();

            //for wallet encryption + change of key
            WALLET_CREDENTIALS =
                    new JSONObject()
                            .put("key", "key")
                            .toString();
        } catch (JSONException e) {
            e.printStackTrace();
        }


        try {
            this.walletHandle = Wallet.openWallet(WALLET_CONFIG, WALLET_CREDENTIALS).get();
        } catch (ExecutionException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch (IndyException e) {
            e.printStackTrace();
        }
        this.mAuth = FirebaseAuth.getInstance();
        this.db = FirebaseDatabase.getInstance();
        this.databaseRef = db.getReference(USER);*/
    }

    public void createNewContextKeys(){

        try {
            System.out.println("create new context keys");
            System.out.println("WALLET HANDLE " + this.walletHandle);
            DidResults.CreateAndStoreMyDidResult myDidResult = null;
            myDidResult = Did.createAndStoreMyDid(this.walletHandle, "{}").get();
            System.out.println("===================> myDidResult:" + myDidResult);
            myDid = myDidResult.getDid();
            System.out.println("===================> DID:" + myDid);
            verkey = Did.keyForLocalDid(this.walletHandle, myDid).get();
            System.out.println("===================> verkey:" + verkey);
        } catch (ExecutionException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch (IndyException e) {
            e.printStackTrace();
        }

    }

    public void createWallet(String uid) {
        final String WALLETName = "MyWallet";
        final String WALLETType = "default";
        String WALLET_CONFIG = null;
        String WALLET_CREDENTIALS = null;

        try {
            WALLET_CONFIG =
                    new JSONObject()
                            .put("id", WALLETName)
                            .put("storage_type", WALLETType)
                            .toString();
            //for wallet encryption + change of key
            WALLET_CREDENTIALS =
                    new JSONObject()
                            .put("key", "key")
                            .toString();
            try {
                Wallet.createWallet(WALLET_CONFIG, WALLET_CREDENTIALS).get();
            } catch (ExecutionException e) {
                System.out.println(e.getMessage());
                if (e.getMessage().indexOf("WalletExistsException") >= 0) {
                    // ignore
                } else {
                    throw new RuntimeException(e);
                }
            }
            this.walletHandle = Wallet.openWallet(WALLET_CONFIG, WALLET_CREDENTIALS).get();
            System.out.println("===================> wallet:" + this.walletHandle);


        } catch (
                IndyException e) {
            e.printStackTrace();
        } catch (
                JSONException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch (ExecutionException e) {
            e.printStackTrace();
        } /*finally {
            if (this.walletHandle != null) {
                try {
                    this.walletHandle.closeWallet().get();
                    //Wallet.deleteWallet(WALLET_CONFIG, WALLET_CREDENTIALS);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }*/
        saveWalletToDB(uid, this.walletHandle);

    }


    public void saveWalletToDB(String userUid, Wallet wallet){
        System.out.println("MyWallet save to bd userUid" + userUid);
        databaseRef.child(userUid).child("wallet").setValue(wallet);
    }

    public String getDid(){
        return myDid;
    }
    public String getVerkey(){
        return verkey;
    }
    public Wallet getMyWalletHandle() { return this.walletHandle; }
}
