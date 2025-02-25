#include <Servo.h>

enum FingerName {
    THUMB_BASE = 0,
    THUMB_TOP,
    FINGER_COUNT
};

class Finger {
private:
    int init_angle;
    int final_angle;
    Servo myservo;
public:
    String name;
    Finger() {}
    Finger(int servo_pin, int init_angle, int final_angle, String name="") {
        this->init_angle = init_angle;
        this->final_angle = final_angle;
        this->name = name;
        this->myservo.attach(servo_pin);
        this->myservo.write(this->init_angle);
    }

    void close() {
        int current_angle = this->myservo.read();
        int dx = this->final_angle - this->init_angle;
        dx = dx/abs(dx);
        int i = current_angle;
        while (i != this->final_angle) {
            this->myservo.write(i);
            i += dx;
        }

    }
    void open() {
        int current_angle = this->myservo.read();
        int dx = this->init_angle - this->final_angle;
        dx = dx/abs(dx);
        int i = current_angle;
        while (i != this->init_angle) {
            this->myservo.write(i);
            i += dx;
        }
    }

    void move_angle(int theta){
        int current_angle = this->myservo.read();
        int dx = theta - current_angle;
        dx = dx/abs(dx);
        int i = current_angle;
        while (i != theta) {
            this->myservo.write(i);
            i += dx;
        }
    }

    void move_percentage(float percentage) {
        if (percentage > 100 || percentage < 0) {
            return;
        }
        int total_anglediff = this->final_angle - this->init_angle;
        float angledelta = percentage*total_anglediff/100.0;

        int new_angle = this->init_angle + angledelta;
        this->move_angle(new_angle);

    }

    int get_percentage() {
        int current_angle = this->myservo.read();
        int total_anglediff = this->final_angle - this->init_angle;
        return (float)(current_angle - this->init_angle)/(total_anglediff) * 100;
    }


    void set_angle(int theta) {
        int small = this->init_angle;
        int large = this->final_angle;
        if (this->init_angle > this->final_angle) {
            small = this->final_angle;
            large = this->init_angle;
        }
        if (theta < large && theta > small) {
            this->myservo.write(theta);
        }
    }

    void set_percentage(float percentage) {
        if (percentage > 1 and percentage < 0) {
            return;
        }
        int total_anglediff = this->final_angle - this->init_angle;
        float angledelta = percentage*total_anglediff/100.0;
        int  new_angle = this->init_angle + angledelta;
        this->set_angle(new_angle);

    }
};

void all_down(Finger* fingers) {
  for (int i = 0; i < FINGER_COUNT; i++) {
        fingers[i].close();
   }
}

void flip_finger(Finger* fingers) {
    all_down(fingers);
}

void all_up(Finger* fingers) {
  for (int i = 0; i < FINGER_COUNT; i++) {
        fingers[i].open();
  }
}


Finger fingers[FINGER_COUNT];

void setup() {
  Serial.begin(250000);

  fingers[THUMB_BASE] = Finger(10, 140, 7, "THUMB_BASE");
  fingers[THUMB_TOP] = Finger(11, 85, 42, "THUMB_TOP");
}

void loop() {
  String buffer = Serial.readStringUntil('\n');\
  
  if (buffer != "") {
    buffer += '\0';
    int func = buffer[0];
    int index;
    switch(func) {
            case 'o':
                index = buffer[1] - 48;
                Serial.println(index);
                if (index > 0 && index < 6) {
                  //Serial.print("OPENING "); Serial.println(index);
                  fingers[index].open();
                  break;
                }
            case 'c':
                index = buffer[1] - 48;
                Serial.println(index);
                if (index > 0 && index < 6) {
                  //Serial.print("OPENING "); Serial.println(index);
                  fingers[index].close();
                  break;
                }
            case 'f':
                //Serial.print("FLIPPP ");
                flip_finger(fingers);break;
            case 'u':
                //Serial.print("ALL UP ");
                all_up(fingers);break;
            case 'd':
                //Serial.print("ALL DOWN ");
                all_down(fingers);break;
            case 'w':
                //Serial.print("GETTING FROM WEBCAM");
                for(int i = 0; i < 5; i++) {
                  int param = buffer.substring(i*3+1, i*3+4).toInt();
                  fingers[i].set_percentage(param);
                }
            default:
                break;
       }
   }
}
          
        
