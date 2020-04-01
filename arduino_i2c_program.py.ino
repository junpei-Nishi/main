// Arduino側テストプログラム

// [想定シナリオ(AからB、またはBのみ)]
// A. Arduino側のスイッチ１を押すとラズパイ側で検査開始
// B. 受診した検査結果に応じて2種類のLEDを光らせる
// スイッチ2が押されると検査を終了（ラズパイのプログラムが終了）

// スイッチやLEDを適宜変更し対応していただければと思います。

#include <Wire.h>

int SLAVE_ADDRESS = 0x04; //I2Cのアドレスを0x04に設定
int greenPin = 13; //13番ピンに緑色LEDが接続されていると想定
int yellowPin = 12; //12番ピンに黄色LEDが接続されていると想定
int sw1 = 11; //11番ピンにスイッチ1が接続されていると想定
int sw2 = 10; //10番ピンにスイッチ2が接続されていると想定

void setup() {  
  // ピンの設定
  pinMode(greenPin, OUTPUT);
  pinMode(yellowPin, OUTPUT);
  pinMode(sw1, INPUT);
  pinMode(sw2, INPUT);

  //I2C接続を開始する
  Wire.begin(SLAVE_ADDRESS);

  //Raspberry Piから何かを受け取るたび、processMessage関数を呼び出す
  Wire.onReceive(processMessage);

//  Raspberry Piから要求された場合に、sendMessage関数を呼び出す
  Wire.onRequest(sendMassage);
}

void loop() {
}

void processMessage(int n) {
  char result = Wire.read();
//  1を受診したら resultOK() を実行
  if (result == '1') {
    resultOK();
//  0を受診したら resultNG() を実行    
  }else if(result == '0') {
    resultNG();
  }
}

void sendMassage() {
//    スイッチ1が押されたら 1 を送信
    if(digitalRead(sw1)==HIGH){
      Wire.write(byte(1));
//    スイッチ2が押されたら 2 を送信      
    }else if(digitalRead(sw2)==HIGH){
      Wire.write(byte(2));
//    何も押されていなければ 0 を送信
    }else{
      Wire.write(byte(0));
    }
}

// 正常品の場合（１が送信されてきた場合）
// 緑色LEDを光らせる
void resultOK() {
  digitalWrite(greenPin, HIGH);
  delay(10000);
  digitalWrite(greenPin, LOW);
}
// 異常品の場合（0が送信されてきた場合）
// 黄色LEDを光らせる
void resultNG() {
  digitalWrite(yellowPin, HIGH);
  delay(10000);
  digitalWrite(yellowPin, LOW);
}
