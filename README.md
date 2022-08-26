# Decentralized digital identity for IoT systems
Decentralized authentication system based on Self-Sovereign Identity to support secure transactions between sporadic interacting IoT devices.

## Brief explanation 

This project consists in a toll gantry and payment system, where a phone plays the role of the equipment in the client's car (OBU) and establishes a connection with a toll gantry equipment (RSU). This channel is sporadic and secure, achieved with TCP sockets.

## Features

This work is under development. However, there are some tasks already achieved:
* OBU connects to RSU network on its own
* OBU sends _connection_request_ to RSU
* RSU send encrypted _connection_response_ to OBU
* OBU receives and decrypt _connection_response_ from RSU

## How to run

1. Start the AP (Network.py file)
2. Run RSU module (RSU.py file) and choose option 2
3. Run OBU module (on Android Studio for example)

## Requirements

* Java 11
* Python 3.8
* Android 8.0 (or higher)

## Connecting Hyperledger Indy with Android

1. Download libindy libraries zip from https://repo.sovrin.org/android
2. Extract the files and put them into the correct jni folder. In this case: app/src/main/jniLibs/arm64-v8a
3. Define source and target compatilities in app/build.gradle
```
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
```
4. Add a [lint.xml](obu/app/lint.xml) file to link JNA 
5. Add libindy's Java wrapper code to  app/src/main/java/org/hyperledger/indy/sdk
6. Set the EXTERNAL_STORAGE environment variable ([Here](obu/app/src/main/java/com/example/myobu/MainActivity.java#L45))
7. Load libindy using JNA: ([Here](obu/app/src/main/java/com/example/myobu/MainActivity.java#L50))

### Credits

Posts/repositories that helped connecting Hyperledger Indy with Android:
* [Hyperledger Indy - sdk](https://github.com/hyperledger/indy-sdk#android)
* [Building binaries of LibIndy for Android](https://github.com/hyperledger/indy-sdk/blob/master/docs/build-guides/android-build.md#usage)
* [Building an Android App with Sovrin](http://ignisvulpis.blogspot.com/2018/08/building-android-app-with-sovrin.html)