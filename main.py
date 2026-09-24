import pandas as pd

def main():
 data = {
 "Месяц": ["Январь", "Февраль", "Март"],
 "Выручка": [120000, 150000, 135000],
 }
 df = pd.DataFrame(data)
 print(df)
 print("Средняя выручка:", df["Выручка"].mean())
if __name__ == "__main__":
 main() 