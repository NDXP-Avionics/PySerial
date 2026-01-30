import serial
import time
from threading import Thread
from rich import print
from rich.console import Console
#from pynput.keyboard import Listener, Key
from xplink import *
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json, random, asyncio

#make console
console = Console()


try:
    ser = serial.Serial('/dev/ttyUSB0', 460800)  # open serial port
except:
    try:
        ser = serial.Serial('/dev/ttyUSB1', 460800) #try other device
    except:
        print("Could not open serial connection!\n")

recievedBytes = 0
start_time = 0
end_time = 0

xp = XPLink()

alphadata = {
    "temps": [None] * 4,
    "pressures": [None] * 12,
    "thrusts": [None] * 1,
    "solenoids": [None] * 4,
    "acc": [None] * 3,
    "keys": [None] * 1,
    "burn": [None] * 1,
    "going": 0,
    "state": 0,
}

def recieve():
    while(1):
        bytes = ser.read()
        packet = xp.XPLINK_UNPACK(bytes[0])
        if(packet):
            #print([hex(pac) for pac in packet.data])
            match xp_msg_t(packet.type).name:
                case "ACC":
                    z_raw = (packet.data[1] << 8) | packet.data[0]
                    y_raw = (packet.data[3] << 8) | packet.data[2]
                    x_raw = (packet.data[5] << 8) | packet.data[4]

                    # Convert to signed 16-bit
                    if z_raw > 32767:
                        z_raw -= 65536
                    if y_raw > 32767:
                        y_raw -= 65536
                    if x_raw > 32767:
                        x_raw -= 65536

                    # Convert from 1/16th degree to actual degrees
                    heading = x_raw / 16.0
                    roll = y_raw / 16.0
                    pitch = z_raw / 16.0

                    alphadata["acc"][0] = heading
                    alphadata["acc"][1] = roll
                    alphadata["acc"][2] = pitch

                case "TEMP1":
                    raw = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("TEMP1: ", raw*1e-4*(9/5)+32)
                    alphadata["temps"][0] = raw * 1e-5

                case "TEMP2":
                    raw = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("TEMP2: ", raw*1e-4*(9/5)+32)
                    alphadata["temps"][1] = raw * 1e-5

                case "TEMP3":
                    raw = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("TEMP3: ", raw*1e-4*(9/5)+32)
                    alphadata["temps"][2] = raw * 1e-5

                case "TEMP4":
                    raw = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("TEMP4: ", raw*1e-4*(9/5)+32)
                    alphadata["temps"][3] = raw * 1e-5

                case "PRESSURE1":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure1: ", data, end='')
                    alphadata["pressures"][0] = data * 1e-5

                case "PRESSURE2":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure2: ", data, end='')
                    alphadata["pressures"][1] = data * 1e-5

                case "PRESSURE3":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure3: ", data, end='')
                    alphadata["pressures"][2] = data * 1e-5

                case "PRESSURE4":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure4: ", data, end='')
                    alphadata["pressures"][3] = data * 1e-5

                case "PRESSURE5":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure5: ", data, end='')
                    alphadata["pressures"][4] = data * 1e-5

                case "PRESSURE6":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure6: ", data, end='')
                    alphadata["pressures"][5] = data * 1e-5

                case "PRESSURE7":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure7: ", data, end='')
                    alphadata["pressures"][6] = data * 1e-5

                case "PRESSURE8":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure8: ", data, end='')
                    alphadata["pressures"][7] = data * 1e-5

                case "PRESSURE9":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure9: ", data, end='')
                    alphadata["pressures"][8] = data * 1e-5

                case "PRESSURE10":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure10: ", data, end='')
                    alphadata["pressures"][9] = data * 1e-5

                case "PRESSURE11":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure11: ", data, end='')
                    alphadata["pressures"][10] = data * 1e-5

                case "PRESSURE12":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[3] << 24 | packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("Pressure12: ", data)
                    alphadata["pressures"][11] = data * 1e-5

                case "THRUST":
                    #print([hex(pac) for pac in packet.data])
                    data = packet.data[2] << 16 | packet.data[1] << 8 | packet.data[0]
                    #print("THRUST:", data)
                    alphadata["thrusts"][0] = data * 1e-5

                case "SOLENOID":
                    #print([hex(pac) for pac in packet.data])
                    s4 = packet.data[0]
                    s3 = packet.data[1]
                    s2 = packet.data[2]
                    s1 = packet.data[3]
                    alphadata["solenoids"][0] = s1
                    alphadata["solenoids"][1] = s2
                    alphadata["solenoids"][2] = s3
                    alphadata["solenoids"][3] = s4

                case "XP_STATE":
                    #print([hex(pac) for pac in packet.data])
                    state = packet.data[0]
                    alphadata["state"] = state

                case "SWITCHES":
                    bw = packet.data[0]
                    k1 = packet.data[1]
                    alphadata["burn"][0] = bw
                    alphadata["keys"][0] = k1

            #print("type:", xp_msg_t(packet.type).name)
            #print("sender:", packet.sender_id)

'''
TIMER
global recievedBytes
global start_time
global end_time
while(1):
    line = ser.read()
    recievedBytes += 1
    #console.print(line.hex())
    if(line.hex() == "00"):
        #console.print("START")
        start_time = time.time()
    if(line.hex() == "ff"):
        #console.print("END")
        end_time = time.time()
        console.print("\rTime: ", end_time - start_time, "seconds")
        console.print("\rRate: ", recievedBytes/(end_time-start_time))
        console.print("\rBytes Recieved: ", recievedBytes)
        recievedBytes = 0
'''

'''
def inthread():
    def on_press(key):
        #print('{0} pressed'.format(key))
        if(key.char == 'f'):
            #send message
            pkt = xp_packet_t()
            pkt.END_BYTE = 0x00
            pkt.sender_id = 0xAA
            pkt.type = 1
            pkt.data = 10
            #send packet
            outpacket = xp.XPLINK_PACK(pkt)
            #serial transmit
            ser.write(bytes(outpacket))
            print("Transmitted\n")
        if(key.char == 'o'):
            #send message
            pkt = xp_packet_t()
            pkt.END_BYTE = 0x00
            pkt.sender_id = 0xAA
            pkt.type = 1
            pkt.data = 333
            #send packet
            outpacket = xp.XPLINK_PACK(pkt)
            #serial transmit
            ser.write(bytes(outpacket))
            print("Transmitted\n")

    def on_release(key):
        #print('{0} release'.format(key))
        if key == Key.esc:
            # Stop listener
            return False

    # Collect events until released
    with Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()
'''

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify your React URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/data")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Send via websocket
    async def send_telemetry():
        
        interval = 0.01  # 100Hz
        next_time = time.time() + interval

        try:
            while True:
                now = time.time()
            
                # Prepare and send data
                data = {
                    "temps": alphadata["temps"][:],
                    "pressures": alphadata["pressures"][:],
                    "thrusts": alphadata["thrusts"][:],
                    "solenoids": alphadata["solenoids"][:],
                    "acc": alphadata["acc"][:],
                    "keys": alphadata["keys"][:],
                    "burn": alphadata["burn"][:],
                    "going": alphadata["going"],
                    "state": alphadata["state"],
                    "time": now
                }
                
                await websocket.send_json(data)

                # calculate next time
                next_time += interval
                sleep_time = next_time - time.time()
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    #reset if running behind
                    next_time = time.time()
                    await asyncio.sleep(0)
                    
        except Exception as e:
            print(f"Sending Error: {e}")

    # Receive via websocket
    async def receive_commands():
        try:
            while True:
                raw_message = await websocket.receive_text()
                data_dict = json.loads(raw_message)
                #print(f"Received command: {data_dict['command']}")

                #send message
                pkt = xp_packet_t()
                pkt.END_BYTE = 0x00
                pkt.sender_id = 0xAA
                pkt.type = 0
                pkt.data = data_dict['command']

                #send packet
                outpacket = xp.XPLINK_PACK(pkt)

                #serial transmit
                ser.write(bytes(outpacket))
                print("Transmitted Command", outpacket, "\n")

        except WebSocketDisconnect:
            print("Client disconnected")
        except Exception as e:
            print(f"Receive Error: {e}")

    # Run both tasks concurrently
    try:
        await asyncio.gather(
            send_telemetry(),
            receive_commands()
        )
    except WebSocketDisconnect:
        print("Connection closed")
    except Exception as e:
        # Ensure one error stops both loops to prevent zombies
        print(f"Connection Error: {e}")

def timer():
    global recievedBytes
    last_time = time.time()
    while(1):
        if(time.time() > last_time + 1):
            console.print("Time: ", time.time())
            console.print("Recieved Bytes: ", recievedBytes)
            last_time = time.time()

def run_uvicorn():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3333,
        log_level="info",
        ws="websockets",
    )

if __name__ == "__main__":
    # Start serial thread
    t1 = Thread(target=recieve, daemon=True)
    t1.start()

    # Start Uvicorn server in a separate thread
    t2 = Thread(target=run_uvicorn, daemon=True)
    t2.start()

    print("System Started. Press CTRL+C to stop.")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        if ser.is_open:
            ser.close()