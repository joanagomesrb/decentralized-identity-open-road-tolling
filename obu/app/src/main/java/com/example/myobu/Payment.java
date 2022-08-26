package com.example.myobu;

import java.util.HashMap;

public class Payment {

    public String date, timestamp, status, iotaAddress;
    public double amount;
    public int count;

    public Payment(int count, String date, String timestamp, double amount, String status, String iotaAddress) {
        this.count = count;
        this.date = date;
        this.timestamp = timestamp;
        this.status = status;
        this.iotaAddress = iotaAddress;
        this.amount = amount;
    }
    public Payment(int count, String timestamp, double amount, String status, String iotaAddress) {
        this.count = count;
        this.timestamp = timestamp;
        this.status = status;
        this.iotaAddress = iotaAddress;
        this.amount = amount;
    }
   /* public Payment(String date, String time, double amount, String status) {
        this.date = date;
        this.timestamp = timestamp;
        this.status = status;
        this.iotaAddress = iotaAddress;
        this.amount = amount;
    }*/

//    public void addPayment(String data, String timestamp, String status, String iotaAddress, double amount){
  //  }

    public String getData() {
        return date;
    }

    public int getCount() {
        return count;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public String getStatus() {
        return status;
    }

    public String getIotaAddress() {
        return iotaAddress;
    }

    public double getAmount() {
        return amount;
    }
}


