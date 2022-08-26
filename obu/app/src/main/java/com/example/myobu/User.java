package com.example.myobu;

import com.google.firebase.database.IgnoreExtraProperties;

import org.hyperledger.indy.sdk.wallet.Wallet;

//@IgnoreExtraProperties
public class User {

    public String username;
    public String email;
    //public String password;
    public MyWallet walletIndy;

    public User() {
        // Default constructor required for calls to DataSnapshot.getValue(User.class)
    }

    public User(String email){
        this.email = email;
    }

    public User(String username, String email, MyWallet walletIndy){
        this.username = username;
        this.email = email;
        //this.password = password;
        this.walletIndy = walletIndy;
    }

    public String getUsername() {
        return username;
    }

    public String getEmail() {
        return email;
    }

    /*public String getPassword() {
        return password;
    }*/

    public MyWallet getWalletIndy() {
        return walletIndy;
    }

    /*public void setPassword(String password) {
        this.password = password;
    }*/
    public void setEmail(String email) {
        this.email = email;
    }
    public void setUsername(String username) {
        this.username = username;
    }
    public void setWalletIndy(MyWallet walletIndy) {
        this.walletIndy = walletIndy;
    }


}

