package com.example.myobu;

import android.annotation.SuppressLint;
import android.content.Context;
import android.content.res.Resources;
import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.CheckBox;
import android.widget.CompoundButton;
import android.widget.EdgeEffect;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.widget.VectorEnabledTintResources;
import androidx.recyclerview.widget.RecyclerView;

import org.w3c.dom.Text;

import java.util.ArrayList;
import java.util.HashMap;

public class PaymentsAdapter extends ArrayAdapter<Payment> {
    public int checkID = 0;
    private Context context;
    HashMap paymentsMap;
    int resource;
    int howMany;
    String userID;
    public HashMap userPayments;
    ArrayList<Payment> paymentsList;
    private CheckboxCheckedListener checkedListener;
    String[] countArray;
    String[] dateArray;
    String[] timeArray;
    String[] amountArray;
    String[] statusArray;
    String[] addrArray;


    public PaymentsAdapter(Context context, int resource, ArrayList<Payment> paymentsList, String userID){
        super(context, resource, paymentsList);
        countArray = new String[paymentsList.size()];
        dateArray = new String[paymentsList.size()];
        timeArray = new String[paymentsList.size()];
        amountArray = new String[paymentsList.size()];
        statusArray = new String[paymentsList.size()];
        addrArray = new String[paymentsList.size()];

        for(int i = 0; i< paymentsList.size(); i++){
            countArray[i] = String.valueOf(paymentsList.get(i).getCount());
            dateArray[i] = paymentsList.get(i).getData();
            timeArray[i] = paymentsList.get(i).getTimestamp();
            amountArray[i] = String.valueOf(paymentsList.get(i).getAmount());
            statusArray[i] = paymentsList.get(i).getStatus();
            addrArray[i] = paymentsList.get(i).getIotaAddress();
        }

        this.paymentsList = paymentsList;
        this.context = context;
        this.resource = resource;
        this.userID = userID;
        this.userPayments = new HashMap();

    }

    class MyViewHolder{
        CheckBox myCheckbox;

        MyViewHolder(View view){
            myCheckbox = (CheckBox) view.findViewById(R.id.checkbox);
        }
    }

    @NonNull
    @Override
    public View getView(int position, @Nullable View convertView, @NonNull ViewGroup parent) {
        View row = convertView;
        MyViewHolder holder = null;

        //int count = getItem(position).count;
        //double amount = getItem(position).amount;
        //String date = getItem(position).date;
        //String time = (String) (getItem(position).timestamp);
        //String status = getItem(position).status;

        TextView countTV = null;
        TextView dateTV = null;
        TextView timeTV = null;
        TextView amountTV = null;
        TextView check = null;

        if(row==null){
            LayoutInflater inflater = (LayoutInflater) context.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            row = inflater.inflate(resource, parent, false);
            holder = new MyViewHolder(row);
            row.setTag(holder);
            LinearLayout linear = (LinearLayout) row.findViewById(R.id.payment_tmp);
            if(statusArray[position].equals("unpaid")) {
                System.out.println("status " + statusArray[position]);
                linear.setBackgroundColor(Color.parseColor("#ffe6e6"));
            }else{
                holder.myCheckbox.setEnabled(false);
            }

        }else{
            holder = (MyViewHolder) row.getTag();
        }

        countTV = (TextView) row.findViewById(R.id.count2);
        dateTV = (TextView) row.findViewById(R.id.date);
        timeTV = (TextView) row.findViewById(R.id.time);
        amountTV = (TextView) row.findViewById(R.id.value);
        check = (TextView) row.findViewById(R.id.checkbox_text);

        countTV.setText(countArray[position]);
        dateTV.setText(dateArray[position]);
        timeTV.setText(timeArray[position]);
        amountTV.setText(amountArray[position]);
        check.setText(statusArray[position]);



        /*if(statusArray[position].equals("paid")){
        }*/

        MyViewHolder finalHolder = holder;
        View finalRow = row;
        holder.myCheckbox.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton compoundButton, boolean b) {
                if(checkedListener != null){
                    boolean checked = finalHolder.myCheckbox.isChecked();
                    System.out.println("cheked a box. checked? : " + checked);
                    checkedListener.getCheckboxCheckedListener(position, checked);
                    int id = finalHolder.myCheckbox.getId();
//                    int tagRow = (int) finalRow.getTag();
                    System.out.println("cheked a box. id: " + id);
                }
            }
        });

        return row;
    }

    public interface CheckboxCheckedListener{
        void getCheckboxCheckedListener(int position, boolean checked);
    }

    public void setCheckedListener(CheckboxCheckedListener checkedListener){
        this.checkedListener = checkedListener;
    }

}
