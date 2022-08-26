package com.example.myobu.ui.login;

public class ToPay {
    String addrToPay;
    double amountToPay;

    public ToPay(String addr, double amount) {
        this.addrToPay = addr;
        this.amountToPay = amount;
    }

    public String getAddressToPay(){
        return this.addrToPay;
    }

    public double getAmountToPay(){
        return this.amountToPay;
    }

}
