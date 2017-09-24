#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import serial
import threading
import time
import serial.tools.list_ports
import logging
import ul_gsm as gsm

global gsm_port  # GSM Port
global s  # GSM Port Serial Instance
global status_reg  # is register network
global status_ #
global redirect_phone
redirect_phone = '+8618708170000'


def rev_sms(sms_id):
    pass


def send_sms(phone, sms):
    send_AT_cmd("AT+CMGF=0")  # 设置PDU格式
    pdu = test2pdu('', phone, sms)
    send_AT_cmd_notline("AT+CMGW="+str(int(len(pdu)/2-1)), ">" , 10, 1)
    cmd_str = pdu
    print("pdu:" + cmd_str)
    s.flush()
    s.write(cmd_str.encode())
    s.write(bytes([0x1A]))
    print("Send SMS")


def handle_call(msg):
    phone = msg.split("\"")[1]
    if(len(phone) < 1):
        logger.error("phone number is invalid.")
        return
    print(phone)
    pass


def handle_sms(msg):
    sms_id = msg.split(",")[1]
    if(len(sms_id) < 1):
        logger.error("sms id is invalid.")
        return
    # Read SMS
    sms_id = int(sms_id)
    sms = read_sms(sms_id)
    if len(sms.sender) <1:
        raise Exception("error to read sms")
    print("sender:" + sms.sender)
    print("text:" + sms.text)
    send_sms(redirect_phone, sms.text)
    # delete_sms(sms_id)


def pdu2text(pdu):
    # sms = gsm.Sms().decode_in('0891683108200805F0040D91688107186720F9000871904251643423184F60597D002B6211000A662F67684E9A5E73000A771F7684')
    # print(sms.smsc, sms.smscType, sms.firstOctet, sms.senderLen, sms.senderType, sms.sender, sms.tpPID, sms.tpDCS)
    # print(sms.year,sms.month,sms.date, sms.hour,sms.minute,sms.second, sms.tz)
    # print(sms.textLen, sms.textBytes, sms.text)
    print("pdu2text:" + pdu)
    return gsm.Sms().decode_in(pdu)


def test2pdu(smsc, sender, text):
    """
    smsc：短信中心号码
    sender：发送人
    text：短信内容
    """
    return gsm.Sms().encode_out({'smsc': smsc, 'sender': sender, 'text': text}).pduHex

def read_sms(sms_id):
    sms_id = int(sms_id)
    cmd_str = "AT+CMGR=" + str(sms_id)
    cmd(cmd_str)

    sms_pdu = ''
    msg_lists = s.readlines()
    k = 0
    while k < 4:
        for i in range(len(msg_lists)):
            if msg_lists[i].decode().find('+CMGR:') > -1:
                sms_pdu = msg_lists[i+1].decode()
                s.flushInput()
                return pdu2text(sms_pdu)
    k +=1




def delete_sms():
    for i in range(50):
        cmd("AT+CMGD="+str(i)+",1")


def delete_sms(id):
    cmd("AT+CMGD="+str(id)+",1")

def parse(rev):
    rev = rev.decode()
    print("rev:"+ rev)
    if rev.find("+CLIP:\"") > -1:
        handle_call(rev)
    if rev.find("+CMTI: \"") > -1:
        handle_sms(rev)
    if rev.find("+CIEV: \"") > -1:
        delete_sms()

    # logging.info(rev)
    # .decode()
    #if()


def cmd(cmd_str):
    s.flushOutput()
    cmd_str = cmd_str + "\r"
    s.write(cmd_str.encode())
    print("CMD: " + cmd_str)

def send_AT_cmd(cmd_str,verify="OK",wait_time=10,interval_time=1):

    print("Send:" + cmd_str)
    cmd_str = cmd_str + "\r"
    i = 0
    while i < wait_time+1:
        s.flush()
        s.write(cmd_str.encode())
        time.sleep(interval_time)
        read_msg = s.readline().decode()
        if read_msg.find(verify) > -1:
            print("Succeed:" + read_msg)
            s.flushInput()
            return 1
        i += 1
    print("Failed: " + str(i))
    s.flushInput()
    return 0
def send_AT_cmd_notline(cmd_str,verify="OK",wait_time=10,interval_time=1):

    print("Send:" + cmd_str)
    cmd_str = cmd_str + "\r"
    i = 0
    while i < wait_time+1:
        s.flush()
        s.write(cmd_str.encode())
        time.sleep(interval_time)
        read_msg = s.read(2).decode()
        if read_msg.find(verify) > -1:
            print("Succeed:" + read_msg)
            s.flushInput()
            return 1
        i += 1
    print("Failed: " + str(i))
    s.flushInput()
    return 0


def init():
    send_AT_cmd("AT+CLIP=1")  # 来电回显
    send_AT_cmd("AT+CMGF=0")    # 设置PDU格式



if __name__== '__main__':
    # sms = gsm.Sms().encode_out({'smsc': '', 'sender': '+8618708176029', 'text': '你好'})
    # print(sms.pduHex)
    # print(sms.pduLen)
    # sms = gsm.Sms().decode_in("0011000D91688107186720F90004AA08607D0A112F689A73")
    # print(sms.smsc, sms.smscType, sms.firstOctet, sms.senderLen, sms.senderType, sms.sender, sms.tpPID, sms.tpDCS)
    # print(sms.year,sms.month,sms.date, sms.hour,sms.minute,sms.second, sms.tz)
    # print(sms.textLen, sms.textBytes, sms.text)
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    logger = logging.getLogger('%s' % 'client')
    gsm_port = ""
    while True:
        try:
            port_list = list(serial.tools.list_ports.comports())
            for port in port_list:
                if port.description.find("CH340") > -1:
                    gsm_port = port.device
            if len(gsm_port) < 1:
                raise Exception("GSM Serial Port Not Found.")
            logger.info("Bind GSM Serial port " + gsm_port)
            s = serial.Serial(gsm_port, 115200, timeout=5)
            #time.sleep(20)
            init()
            print("Listening...")
            send_sms(redirect_phone, "hello")
            while True:
                # read_sms(1)
                parse(s.readline())
        except Exception as e:
            logger.error(str(e))
            time.sleep(1)
            if 's' in locals().keys():
                s.close()
            continue


