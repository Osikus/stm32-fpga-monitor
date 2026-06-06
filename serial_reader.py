import serial
import time
import re
import csv
import os
from datetime import datetime

SERIAL_PORT = "COM9"
BAUD_RATE = 115200
CSV_FILE = "data.csv"

def parse_line(line):
    """
    解析格式：
    TEMP: 26.07 C, HUMI: 53.26 %, LIGHT: 55.00 lx
    """
    pattern = (
        r"TEMP:\s*([-+]?\d+(?:\.\d+)?)\s*C,\s*"
        r"HUMI:\s*([-+]?\d+(?:\.\d+)?)\s*%,\s*"
        r"LIGHT:\s*([-+]?\d+(?:\.\d+)?)\s*lx"
    )

    match = re.search(pattern, line)

    if match:
        temperature = float(match.group(1))
        humidity = float(match.group(2))
        light = float(match.group(3))

        return temperature, humidity, light

    return None, None, None

def save_to_csv(temp, humi, light):
    file_exists = os.path.exists(CSV_FILE)

    with open(
        CSV_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(
                ["time", "temp", "humi", "light"]
            )

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        writer.writerow(
            [now, temp, humi, light]
        )

def main():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

    save_interval = 5
    last_save_time = 0

    print("串口读取程序已启动")
    print(f"正在监听 {SERIAL_PORT} ...")
    print(f"每 {save_interval} 秒保存一次数据")
    print("按 Ctrl+C 停止程序")

    try:
        while True:
            line = ser.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            if not line:
                continue

            temp, humi, light = parse_line(line)

            current_time = time.time()

            if (
             temp is not None
             and humi is not None
             and light is not None
            ):
                if current_time - last_save_time >= save_interval:
                    save_to_csv(temp, humi, light)
                    last_save_time = current_time

                    print(
                   f"已保存：温度={temp:.2f}℃，"
                   f"湿度={humi:.2f}%，"
                   f"光照={light:.2f} lx"
                    )

    except KeyboardInterrupt:
        print("\n程序已停止")

    finally:
        ser.close()
        print("串口已关闭")


if __name__ == "__main__":
    main()