import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = r"output"
PLOTS_DIR = r"plots"
PLOT_PATH = os.path.join(OUTPUT_DIR, PLOTS_DIR)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PLOT_PATH, exist_ok=True)


# --- Load Data ---
if not os.path.exists("lab_data.csv"):
    raise FileNotFoundError("File not found")

if "lab_data.csv".endswith(".csv"):
    df = pd.read_csv("lab_data.csv")
elif "lab_data.csv".endswith(".xlsx"):
    df = pd.read_excel("lab_data.csv")
else:
    raise ValueError("Only CSV or Excel files are supported")


# --- Cleaning: DROP_DUPLICATES ---
df = df.drop_duplicates()

# --- Cleaning: DROP_ALL ---
df = df.dropna()
df = df[df["age"] > 15]
df['result'] = df.eval('''((0.1 * glucose) + (0.9 * cholesterol))''')
df = df.rename(columns={"result": "sick"})
df['res'] = df.eval('''sick''')

# --- Min-Max Normalization ---
col_min = df["res"].min()
col_max = df["res"].max()
df["res"] = (df["res"] - col_min) / (col_max - col_min)


# --- Plotting HEATMAP ---
plt.figure(figsize=(10, 6))
corr = df.select_dtypes(include=["number"]).corr()
sns.heatmap(corr, annot=True, cmap="coolwarm")
plt.title("Correlation Heatmap")
plt.tight_layout()
plt.savefig(r"output\plots\heatmap_df.png", dpi=150)  # === CHANGE 2: Added dpi for better quality ===
plt.close()  # === CHANGE 3: Always close figure to free memory ===

df = df.sort_values(by="sick", ascending=True)

# --- Leveling Of res From df ---
bins = [0.0, 0.3, 0.6, 0.8]
bins.append(float('inf'))
labels = ['low', 'normal', 'heigh', 'danger']
df["res_level"] = pd.cut(df["res"], bins=bins, labels=labels, right=False)


# --- Plotting SCAT ---
plt.figure(figsize=(10, 6))
plt.scatter(df["res"], df["age"], edgecolors="black", s=50)
plt.title("Scatter of res by age")
plt.tight_layout()
plt.savefig(r"output\plots\scat_res_in_age.png", dpi=150)  # === CHANGE 2: Added dpi for better quality ===
plt.close()  # === CHANGE 3: Always close figure to free memory ===


# --- Save DataFrame ---
save_path = os.path.join(OUTPUT_DIR, "processed_data.csv")
if "processed_data.csv".endswith(".csv"):
    df.to_csv(save_path, index=False)
elif "processed_data.csv".endswith(".xlsx"):
    df.to_excel(save_path, index=False)
elif "processed_data.csv".endswith(".json"):
    df.to_json(save_path, orient="records")
else:
    raise ValueError("Supported formats: .csv, .xlsx, .json")
