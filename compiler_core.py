# -*- coding: utf-8 -*-
"""
Final Term Project
Persian DSL Compiler
→ Python Code + Statistical Report + Plots + AST Visualization
[MINIMAL CHANGES FOR GUI INTEGRATION]
"""

import re
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from lark import Lark, Transformer
from datetime import datetime
import subprocess

# =====================================================
# 1. Persian → English DSL Mapper
# =====================================================

class PersianToDSLMapper:
    def __init__(self):
        self.rules = [
            (r'بگیر از "([^"]+)" به نام (\w+)', r'LOAD "\1" INTO \2'),
            (r'خلاصه (\w+)', r'DESCRIBE \1'),
            (r'نمایش (\w+) : (\d+) سطر اول', r'HEAD \1 \2'),

            (r'پاکسازی (\w+) : حذف تکراری', r'CLEAN \1 DROP_DUPLICATES'),
            (r'پاکسازی (\w+) : حذف کلی (خالی|پرت)', r'CLEAN \1 DROP_ALL \2'),
            (r'پاکسازی (\w+) : حذف (\w+) (خالی|پرت)', r'CLEAN \1 DROP_SPECIFIC \2 \3'),
            (r'پاکسازی (\w+) : جایگزینی کلی (خالی|پرت) با (میانگین|مد)', r'CLEAN \1 FILL_ALL \2 \3'),
            (r'پاکسازی (\w+) : جایگزینی (\w+) (خالی|پرت) با (میانگین|مد)', r'CLEAN \1 FILL_SPECIFIC \2 \3 \4'),

            (r'کپی (\w+) : در (\w+)', r'DUPLICATE \1 TO \2'),
            (r'ذخیره (\w+) : در "([^"]+)"', r'SAVE \1 TO "\2"'),
            (r'محاسبه (\w+) : میانگین (\w+)', r'CALC \1 MEAN "OF" \2'),
            (r'محاسبه (\w+) : انحراف_معیار (\w+)', r'CALC \1 STD "OF" \2'),

            (r'نمودار (\w+) : (هیستوگرام|میانگین|خطی|پراکندگی|جعبه‌ای) (\w+)(?: در (\w+))?', r'PLOT \1 \2 OF \3 IN \4'),
            (r'نمودار (\w+) : نقشه_حرارتی', r'PLOT \1 HEATMAP OF ALL IN ALL'),

            (r'فیلتر (\w+) : وقتی (\w+) (>=|<=|==|!=|>|<) ("[^"]+"|\d+(\.\d+)?)', r'FILTER \1 WHERE \2 \3 \4'),
            (r'فیلتر (\w+) : (\w+) بین (\d+(\.\d+)?) و (\d+(\.\d+)?)', r'FILTER_RANGE \1 \2 \3 \5'),
            (r'فیلتر_ترکیبی (\w+) : (.+)', r'FILTER_COMPLEX \1 \2'),

            (r'جستجو (\w+) : در (\w+) شامل "([^"]+)"', r'SEARCH \1 IN \2 CONTAINS "\3"'),

            (r'سطح_بندی (\w+) : در (\w+) به ((?:\d+(?:\.\d+)?:\w+\s*)+)', r'LEVELING \1 \2 \3'),
            (r'مرتب_سازی (\w+) : (\w+) (صعودی|نزولی)', r'SORT \1 BY \2 \3'),
            (r'گروه_بندی (\w+) : بر اساس (\w+) (میانگین|جمع|تعداد|حداکثر|حداقل) (\w+)', r'GROUPBY \1 BY \2 OP \3 OF \4'),

            (r'ادغام (\w+) و (\w+) : بر اساس (\w+)', r'MERGE \1 AND \2 ON \3'),
            (r'ایجاد_ستون (\w+) : (\w+) = (.+)', r'CREATE_COL \1 : \2 = \3'),
            (r'حذف_ستون (\w+) : (\w+)', r'DROP_COL \1 \2'),
            
            (r'تغییر_نام (\w+) : (\w+) به (\w+)', r'RENAME \1 COL \2 TO \3'),
            (r'تبدیل_زمان (\w+) : ستون (\w+)', r'CONVERT_TIME \1 COL \2'),
            (r'نرمال_سازی (\w+) : ستون (\w+)', r'NORMALIZE \1 COL \2'),
            (r'همبستگی (\w+) : بین (\w+) و (\w+)', r'CORRELATE \1 BETWEEN \2 AND \3'),
        ]

    def translate(self, text):
        for p, r in self.rules:
            text = re.sub(p, r, text)
        return text.strip()


# =====================================================
# 2. Grammar Definition
# =====================================================

grammar = r"""
start: statement+

statement: load_stmt
         | duplicate_stmt
         | save_stmt
         | clean_stmt
         | calc_stmt
         | plot_stmt
         | filter_stmt
         | filter_range_stmt
         | level_stmt
         | sort_stmt
         | groupby_stmt
         | drop_col_stmt
         | describe_stmt
         | head_stmt
         | filter_complex_stmt
         | search_stmt
         | merge_stmt
         | create_col_stmt
         | rename_stmt
         | convert_time_stmt
         | normalize_stmt
         | corr_stmt

load_stmt: "LOAD" STRING "INTO" ID


clean_stmt: "CLEAN" ID clean_op

clean_op: drop_all
        | drop_specific
        | fill_all
        | fill_specific
        | drop_duplicates

drop_all: "DROP_ALL" TARGET
drop_specific: "DROP_SPECIFIC" ID TARGET
fill_all: "FILL_ALL" TARGET METHOD
fill_specific: "FILL_SPECIFIC" ID TARGET METHOD
drop_duplicates: "DROP_DUPLICATES"

TARGET: "خالی" | "پرت" | "null" | "outlier"
METHOD: "میانگین" | "مد" | "mean" | "mode"

DROP_ALL: "DROP_ALL"
DROP_SPECIFIC: "DROP_SPECIFIC"
FILL_ALL: "FILL_ALL"
FILL_SPECIFIC: "FILL_SPECIFIC"

duplicate_stmt: "DUPLICATE" ID "TO" ID
save_stmt: "SAVE" ID "TO" STRING

calc_stmt: "CALC" ID calc_op+
calc_op: MEAN "OF" ID
          | STD "OF" ID

plot_stmt: "PLOT" ID PLOT_TYPE "OF" (ID|ALL) "IN" (ID|ALL)
PLOT_TYPE: "هیستوگرام" | "میانگین" | "خطی" | "پراکندگی" | "جعبه‌ای" | "HEATMAP"
         | "HIST" | "MEAN" | "LINE" | "SCAT" | "BOX"
ALL: "ALL"

filter_stmt: "FILTER" ID "WHERE" ID COMP (STRING|NUMBER)
filter_range_stmt: "FILTER_RANGE" ID ID NUMBER NUMBER

filter_complex_stmt: "FILTER_COMPLEX" ID CONDITION_EXPR
CONDITION_EXPR: /.+/

search_stmt: "SEARCH" ID "IN" ID "CONTAINS" STRING

level_stmt: "LEVELING" ID ID level_op+
level_op : NUMBER ":" ID

sort_stmt: "SORT" ID "BY" ID ORDER
ORDER: "صعودی" | "نزولی" | "DES" | "ASC"


groupby_stmt: "GROUPBY" ID "BY" ID "OP" AGG_FUNC "OF" ID
AGG_FUNC: "میانگین" | "جمع" | "تعداد" | "حداکثر" | "حداقل" 
          | "mean" | "sum" | "count" | "max" | "min"

merge_stmt: "MERGE" ID "AND" ID "ON" ID       
create_col_stmt: "CREATE_COL" ID ":" ID "=" EXPRESSION
EXPRESSION: /.+/
drop_col_stmt: "DROP_COL" ID ID
rename_stmt: "RENAME" ID "COL" ID "TO" ID
convert_time_stmt: "CONVERT_TIME" ID "COL" ID

describe_stmt: "DESCRIBE" ID
head_stmt: "HEAD" ID INT

normalize_stmt: "NORMALIZE" ID "COL" ID
corr_stmt: "CORRELATE" ID "BETWEEN" ID "AND" ID


MEAN: "MEAN"
STD: "STD"




ID: /[_a-zA-Z\u0600-\u06FF][a-zA-Z0-9_\u0600-\u06FF\u06F0-\u06F9]*/
STRING: /"[^"]*"/
COMP: ">" | "<" | ">=" | "<=" | "==" | "!="
NUMBER: /[0-9]+(\.[0-9]+)?/
INT: /[0-9]+/

%import common.WS
%ignore WS
"""


# =====================================================
# 3. AST → Graphviz (.dot)
# =====================================================

def ast_to_dot(tree, output_name="ast", output_dir="outputs"):
    """
    Generates AST image (PNG) using Graphviz and saves it in outputs directory.
    """

    os.makedirs(output_dir, exist_ok=True)
    dot_path = os.path.join(output_dir, f"{output_name}.dot")
    img_path = os.path.join(output_dir, f"{output_name}.png")
    node_id = 0
    lines = [
        "digraph AST {",
        "node [shape=box, fontname=\"Helvetica\"];"
    ]

    def visit(node, parent=None):
        nonlocal node_id
        my_id = node_id
        label = node.data if hasattr(node, "data") else str(node)
        # Escape quotes for Graphviz
        label = label.replace('"', '\\"')
        lines.append(f'node{my_id} [label="{label}"];')
        if parent is not None:
            lines.append(f'node{parent} -> node{my_id};')
        node_id += 1
        if hasattr(node, "children"):
            for child in node.children:
                visit(child, my_id)
    visit(tree)
    lines.append("}")

    # Write DOT file
    with open(dot_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Convert DOT to PNG
    subprocess.run(
        ["dot", "-Tpng", dot_path, "-o", img_path],
        check=True
    )


# =====================================================
# 4. Code Generator (Transformer)
# =====================================================

class CodeGenerator(Transformer):
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.plots_dir = os.path.join(output_dir, "plots")
        os.makedirs(self.plots_dir, exist_ok=True)

        self.current_var = None

        self.report_lines = []
        self.log_counter = 1

    def statement(self, items):
        return items[0]

    def start(self, items):
        return "\n".join(items)
    
    def add_log(self, title, body=""):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        block = f"[{self.log_counter}] {title}\n{body}\n\nTimestamp: {ts}\n"
        self.report_lines.append(block)
        self.log_counter += 1


    # ---------- LOAD ----------
    def load_stmt(self, items):
        file_path, var = items
        self.current_var = var

        # try to get counts at compile time if file exists
        file_name = str(file_path).strip('"')
        body = f"Loaded file: {file_name}\n"
        try:
            if os.path.exists(file_name):
                if file_name.lower().endswith(".csv"):
                    df_tmp = pd.read_csv(file_name)
                elif file_name.lower().endswith((".xls", ".xlsx")):
                    df_tmp = pd.read_excel(file_name)
                else:
                    df_tmp = None
                if df_tmp is not None:
                    body += f"Rows: {len(df_tmp)}\nCols: {df_tmp.shape[1]}\n"
        except Exception:
            pass

        self.add_log("LOAD", body.strip())

        return f'''
# --- Load Data ---
if not os.path.exists({file_path}):
    raise FileNotFoundError("File not found")

if {file_path}.endswith(".csv"):
    {var} = pd.read_csv({file_path})
elif {file_path}.endswith(".xlsx"):
    {var} = pd.read_excel({file_path})
else:
    raise ValueError("Only CSV or Excel files are supported")
'''
    
    # ---------- INFORMATION ----------
    def describe_stmt(self, items):
        var = items[0]
        self.add_log("DESCRIBE", f"Performed describe on: {var}")
        return f'print({var}.describe())'

    def head_stmt(self, items):
        var, n = items
        self.add_log("HEAD", f"Shown first {n} rows of {var}")
        return f'print({var}.head({n}))'

    # ---------- DUPLICATE-SAVE ----------
    def duplicate_stmt(self, items):
        source,dest = items
        self.add_log("DUPLICATE", f"Copied {source} to {dest}")
        return f"\n{dest}={source}.copy()\n"
    
    def save_stmt(self, items):
        var, filename = items
        self.add_log("SAVE", f"Saved {var} to {filename}")
        return f'''
# --- Save DataFrame ---
save_path = os.path.join(OUTPUT_DIR, {filename})
if {filename}.endswith(".csv"):
    {var}.to_csv(save_path, index=False)
elif {filename}.endswith(".xlsx"):
    {var}.to_excel(save_path, index=False)
elif {filename}.endswith(".json"):
    {var}.to_json(save_path, orient="records")
else:
    raise ValueError("Supported formats: .csv, .xlsx, .json")
'''


    # ---------- CLEAN ----------
    def clean_stmt(self, items):
        var = str(items[0])
        op_node = items[1]
        actual_op = op_node.children[0]
        op_type = actual_op.data.upper()
        params = [str(c) for c in actual_op.children]
        
        self.add_log(f"CLEAN - {op_type}", f"Params: {' '.join(params)}")

        def get_method(m): return 'mean' if m in ['میانگین', 'mean'] else 'mode'
        def is_outlier(target): return target in ['پرت', 'outlier']

        code = f"\n# --- Cleaning: {op_type} ---\n"

        if op_type == "DROP_DUPLICATES":
            code += f"{var} = {var}.drop_duplicates()"

        elif op_type == "DROP_ALL":
            target = params[0]
            if is_outlier(target):
                code += f"""for col in {var}.select_dtypes(include=['number']).columns:
    q1, q3 = {var}[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    {var} = {var}[({var}[col] >= q1-1.5*iqr) & ({var}[col] <= q3+1.5*iqr)]"""
            else:
                code += f"{var} = {var}.dropna()"

        elif op_type == "DROP_SPECIFIC":
            col, target = params
            if is_outlier(target):
                code += f"""q1, q3 = {var}['{col}'].quantile([0.25, 0.75])
iqr = q3 - q1
{var} = {var}[({var}['{col}'] >= q1-1.5*iqr) & ({var}['{col}'] <= q3+1.5*iqr)]"""
            else:
                code += f"{var} = {var}.dropna(subset=['{col}'])"

        elif op_type == "FILL_ALL":
            target, method = params
            m = get_method(method)
            val_logic = f"{var}[col].mode()[0]" if m == 'mode' else f"{var}[col].mean()"
            
            if is_outlier(target):
                code += f"""for col in {var}.select_dtypes(include=['number']).columns:
    q1, q3 = {var}[col].quantile([0.25, 0.75]); iqr = q3 - q1
    low, high = q1-1.5*iqr, q3+1.5*iqr
    {var}.loc[({var}[col] < low) | ({var}[col] > high), col] = {val_logic}"""
            else:
                code += f"""for col in {var}.columns:
    {var}[col] = {var}[col].fillna({val_logic})"""

        elif op_type == "FILL_SPECIFIC":
            col, target, method = params
            m = get_method(method)
            val_calc = f"{var}['{col}'].mode()[0]" if m == 'mode' else f"{var}['{col}'].mean()"
            
            if is_outlier(target):
                code += f"""q1, q3 = {var}['{col}'].quantile([0.25, 0.75]); iqr = q3 - q1
low, high = q1-1.5*iqr, q3+1.5*iqr
{var}.loc[({var}['{col}'] < low) | ({var}['{col}'] > high), '{col}'] = {val_calc}"""
            else:
                code += f"{var}['{col}'] = {var}['{col}'].fillna({val_calc})"

        return code

    # ---------- CALC ----------
    def calc_op(self, items):
        return (items[0].type, str(items[1]))

    def calc_stmt(self, items):
        var = items[0]
        lines = []

        for op, col in items[1:]:
            if op == "MEAN":
                lines.append(f'mean_{col} = {var}["{col}"].mean()')

                self.report_lines.append(f"Mean of {col}: {{mean_{col}:.2f}}")
                self.add_log("CALC", f"Mean of {col}")

            elif op == "STD":
                lines.append(f'std_{col} = {var}["{col}"].std()')
                self.report_lines.append(f"Standard deviation of {col}: {{std_{col}:.2f}}")
                self.add_log("CALC", f"STD of {col}")

        return "\n".join(lines)

    # ---------- PLOTS ----------
    def plot_stmt(self, items):
        var, plot_type, target_col, group_col = [str(i) for i in items]
        
        type_map = {
            "هیستوگرام": "HIST", "HIST": "HIST",
            "میانگین": "MEAN", "MEAN": "MEAN",
            "خطی": "LINE", "LINE": "LINE",
            "پراکندگی": "SCAT", "SCAT": "SCAT",
            "جعبه‌ای": "BOX", "BOX": "BOX",
            "HEATMAP": "HEATMAP"
        }
        
        selected_type = type_map.get(plot_type, "HIST")
        plot_code = ""
        path = ""

        self.add_log("PLOT", f"Type: {selected_type}\nTarget: {target_col}\nGroup: {group_col}")

        if selected_type == "HIST":
            path = os.path.join(self.plots_dir, f"hist_{target_col}.png")
            plot_code = f'{var}["{target_col}"].hist(bins=20)\nplt.title("Histogram of {target_col}")'
            
        elif selected_type == "MEAN":
            path = os.path.join(self.plots_dir, f"mean_{target_col}_by_{group_col}.png")
            plot_code = f'{var}.groupby("{group_col}")["{target_col}"].mean().plot(kind="bar")\nplt.title("Mean {target_col} by {group_col}")'

        elif selected_type == "LINE":
            path = os.path.join(self.plots_dir, f"line_{target_col}_{group_col}.png")
            plot_code = f'plt.plot({var}["{target_col}"], {var}["{group_col}"], color="red")\nplt.title("Trend: {target_col} vs {group_col}")'

        elif selected_type == "BOX":
            path = os.path.join(self.plots_dir, f"box_{target_col}_by_{group_col}.png")
            plot_code = f'{var}.boxplot(column="{target_col}", by="{group_col}")\nplt.title("Distribution of {target_col} by {group_col}")\nplt.suptitle("")'

        elif selected_type == "HEATMAP":
            path = os.path.join(self.plots_dir, f"heatmap_{var}.png")
            plot_code = f'corr = {var}.select_dtypes(include=["number"]).corr()\nsns.heatmap(corr, annot=True, cmap="coolwarm")\nplt.title("Correlation Heatmap")'
        elif selected_type == "SCAT":
            path = os.path.join(self.plots_dir, f"scat_{target_col}_in_{group_col}.png")
            plot_code = f'plt.scatter({var}["{target_col}"], {var}["{group_col}"], edgecolors="black", s=50)\nplt.title("Scatter of {target_col} by {group_col}")'

        # === CHANGE 1: REMOVED plt.show() to prevent GUI freezing ===
        return f'''
# --- Plotting {selected_type} ---
plt.figure(figsize=(10, 6))
{plot_code}
plt.tight_layout()
plt.savefig(r"{path}", dpi=150)  # === CHANGE 2: Added dpi for better quality ===
plt.close()  # === CHANGE 3: Always close figure to free memory ===
'''

    # ---------- FILTERS ----------
    def filter_stmt(self, items):
        var, col, op, val = items

        self.add_log("FILTER", f"Condition: {col} {op} {val}")
        return f'{var} = {var}[{var}["{col}"] {op} {val}]'
    
    def filter_range_stmt(self, items):
        var, col, low, high = items
        self.add_log("FILTER_RANGE", f"{col} between {low} and {high}")
        return f'{var} = {var}[({var}["{col}"] >= {low}) & ({var}["{col}"] <= {high})]'
    
    def filter_complex_stmt(self, items):
        var, raw_condition = items

        condition = str(raw_condition).replace(" و ", " & ").replace(" یا ", " | ")
        self.add_log("FILTER_COMPLEX", f"Condition: {condition}")
        return f"{var} = {var}.query('''{condition}''')"

    # ---------- SEARCH ----------
    def search_stmt(self, items):
        var, col, val = items

        val_clean = str(val).replace('"', '')
        self.add_log("SEARCH", f"Search: {col} contains {val_clean}")
        return f'{var} = {var}[{var}["{col}"].str.contains("{val_clean}", na=False, case=False)]'
    
    # ---------- LEVELING ----------
    def level_op(self, items):
        return (float(items[0]), str(items[1]))
    
    def level_stmt(self, items):
        val = items[0]
        col = items[1]
        levels = items[2:]

        levels = sorted(levels, key=lambda x: x[0])

        bins = [v for v, _ in levels]
        labels = [label for _, label in levels]

        new_col = f"{col}_level"

        self.add_log("LEVELING", f"Column: {col}\nLevels: {labels}")

        return f'''
# --- Leveling Of {col} From {val} ---
bins = {bins}
bins.append(float('inf'))
labels = {labels}
{val}["{new_col}"] = pd.cut({val}["{col}"], bins=bins, labels=labels, right=False)
'''
    
    # ---------- SORT ----------
    def sort_stmt(self, items):
        var, col, order = items
        ascending = "True" if order in ["صعودی","ASC"] else "False"
        self.add_log("SORT", f"Sort by {col} ({order})")
        return f'{var} = {var}.sort_values(by="{col}", ascending={ascending})'
    
    # ---------- GROUP-BY ----------
    def groupby_stmt(self, items):
        var, group_col, op_persian, target_col = items
        ops_map = {
        "میانگین": "mean",
        "جمع": "sum",
        "تعداد": "count",
        "حداکثر": "max",
        "حداقل": "min",
        "mean": "mean",
        "sum": "sum",
        "count": "count",
        "max": "max",
        "min": "min"
    }
    
        op_eng = ops_map.get(str(op_persian), "mean")

        self.add_log("GROUPBY", f"Grouped by: {group_col}\nOperation: {op_eng}\nTarget: {target_col}")
    
        return f'''
# --- GroupBy: {op_eng} {target_col} by {group_col} ---
print(f"\\nreport{op_eng} {target_col} according to {group_col}:")
result = {var}.groupby("{group_col}")["{target_col}"].{op_eng}()
print(result)
'''
    
    # ---------- CRUD ----------
    def merge_stmt(self, items):
        df1, df2, key = items
        self.add_log("MERGE", f"Merged {df1} and {df2} on {key}")
        return f'{df1} = pd.merge({df1}, {df2}, on="{key}", how="inner")'

    def create_col_stmt(self, items):
        var, new_col, expr = items
        self.add_log("CREATE_COL", f"Created column: {new_col} in {var}")
        return f"{var}['{new_col}'] = {var}.eval('''{expr}''')"
    
    def drop_col_stmt(self, items):
        var, col = items
        self.add_log("DROP_COL", f"Dropped column: {col} from {var}")
        return f'{var} = {var}.drop(columns=["{col}"])'
    
    def rename_stmt(self, items):
        var, old_name, new_name = items
        self.add_log("RENAME", f"Renamed column {old_name} to {new_name} in {var}")
        return f'{var} = {var}.rename(columns={{"{old_name}": "{new_name}"}})'
    
    def convert_time_stmt(self, items):
        var, col = items
        self.add_log("CONVERT_TIME", f"Converted column {col} to datetime in {var}")
        return f'{var}["{col}"] = pd.to_datetime({var}["{col}"])'
    
    # ---------- NORMALIZE ----------
    def normalize_stmt(self, items):
        var, col = items
        self.add_log("NORMALIZE", f"Normalized column: {col} in {var}")
        return f'''
# --- Min-Max Normalization ---
col_min = {var}["{col}"].min()
col_max = {var}["{col}"].max()
{var}["{col}"] = ({var}["{col}"] - col_min) / (col_max - col_min)
'''
    
    # ---------- CORRELATION ----------
    def corr_stmt(self, items):
        var, col1, col2 = items
        self.add_log("CORRELATE", f"Columns: {col1} & {col2}")
        return f'''
# --- Correlation Analysis ---
corr_val = {var}["{col1}"].corr({var}["{col2}"])
print(f"\\nMeasure of correlation of {col1} and {col2}: {{corr_val:.4f}}")
'''

# =====================================================
# 5. Compiler Pipeline (MODIFIED FOR GUI INTEGRATION)
# =====================================================

def run_compiler(persian_code, capture_output=True):
    """
    Runs the compiler pipeline.
    
    Args:
        persian_code: Persian DSL code as string
        capture_output: If True, captures stdout/stderr instead of printing
    
    Returns:
        tuple: (success: bool, output_log: str, error_msg: str)
    """
    import sys
    import io
    
    OUTPUT_DIR = "output"
    PLOTS_DIR = "plots"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Capture output only when requested (GUI mode)
    if capture_output:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured = io.StringIO()
        sys.stdout = sys.stderr = captured
    
    try:
        mapper = PersianToDSLMapper()
        dsl_code = mapper.translate(persian_code)

        if capture_output:
            captured.write("✓ Intermediate DSL code generated:\n")
            captured.write(dsl_code + "\n\n")
        else:
            print("Intermediate DSL code:\n", dsl_code)

        parser = Lark(grammar, parser="lalr")
        ast_tree = parser.parse(dsl_code)
        ast_to_dot(ast_tree, output_name="ast", output_dir=OUTPUT_DIR)

        generator = CodeGenerator(OUTPUT_DIR)
        python_code = generator.transform(ast_tree)

        gen_path = os.path.join("./", "generated_code.py")
        with open(gen_path, "w", encoding="utf-8") as f:
            f.write("import pandas as pd\nimport matplotlib.pyplot as plt\nimport os\nimport seaborn as sns\nimport warnings\nwarnings.filterwarnings('ignore')\n\n")

            # Output folders
            f.write(f'OUTPUT_DIR = r"{OUTPUT_DIR}"\n')
            f.write(f'PLOTS_DIR = r"{PLOTS_DIR}"\n')
            f.write(f'PLOT_PATH = os.path.join(OUTPUT_DIR, PLOTS_DIR)\n\n')
            
            # Make sure folders exist
            f.write('os.makedirs(OUTPUT_DIR, exist_ok=True)\n')
            f.write('os.makedirs(PLOT_PATH, exist_ok=True)\n\n')
            
            # Generated code from AST
            f.write(python_code)

        env = {
        "pd": pd,
        "plt": plt,
        "os": os,
        "sns": sns,
        "OUTPUT_DIR": OUTPUT_DIR,
        "PLOTS_DIR": PLOTS_DIR,
        "PLOT_PATH": os.path.join(OUTPUT_DIR, PLOTS_DIR)
        }
        exec(python_code, env)

        # Generate report with actual values
        report_path = os.path.join(OUTPUT_DIR, "report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("گزارش آماری پردازش داده‌ها (Persian DSL Compiler)\n")
            f.write("=" * 50 + "\n\n")
            for line in generator.report_lines:
                try:
                    f.write(line.format(**env) + "\n\n")
                except Exception:
                    f.write(line + "\n\n")
        
        if capture_output:
            # Append report content to output
            captured.write("\n" + "="*50 + "\n")
            captured.write("محتوای گزارش کامل (report.txt):\n")
            captured.write("="*50 + "\n")
            with open(report_path, "r", encoding="utf-8") as f:
                captured.write(f.read())
            
            # Success summary
            plots_count = len([f for f in os.listdir(generator.plots_dir) if f.endswith('.png')]) if os.path.exists(generator.plots_dir) else 0
            captured.write(f"\nکامپایل با موفقیت انجام شد!\n")
            captured.write(f"فایل کد پایتون: {OUTPUT_DIR}/generated_code.py\n")
            captured.write(f"تعداد نمودارهای تولید شده: {plots_count}\n")
            captured.write(f"مسیر نمودارها: {OUTPUT_DIR}/{PLOTS_DIR}/\n")
            captured.write(f"گزارش کامل: {OUTPUT_DIR}/report.txt\n")
            captured.write(f"درخت تحلیل (AST): {OUTPUT_DIR}/ast.png\n")
        
        return (True, captured.getvalue() if capture_output else "", "")
    
    except Exception as e:
        import traceback
        error_msg = f"خطای کامپایل:\n{str(e)}\n\nجزئیات:\n{traceback.format_exc()}"
        if capture_output:
            captured.write("\n" + "="*50 + "\n")
            captured.write("خطا در پردازش:\n")
            captured.write("="*50 + "\n")
            captured.write(error_msg)
            return (False, captured.getvalue(), str(e))
        else:
            raise
    finally:
        if capture_output:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


# =====================================================
# 6. CLI Mode (UNCHANGED - Preserved for backward compatibility)
# =====================================================

def get_user_input():
    print("""========================================
 Persian / English DSL Compiler
========================================
HINT: You may mix Persian and English DSL commands in the same script.
----------------------------------------
""")

    # 2) input method
    print("Select input method:")
    print(" 1) Enter code manually")
    print(" 2) Load code from text file")
    method_choice = input("Your choice (1/2): ").strip()

    if method_choice == "1":
        print("\nEnter the DSL code (empty line to finish):")
        lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        code = "\n".join(lines)

    elif method_choice == "2":
        path = input("Enter .txt file path: ").strip()
        if not os.path.exists(path):
            raise FileNotFoundError("Input file not found")
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
    else:
        raise ValueError("Invalid input method")

    return code


# =====================================================
# 7. Main (UNCHANGED - CLI mode preserved)
# =====================================================

if __name__ == "__main__":
    import sys
    # Only run CLI mode if not imported as module
    if not sys.modules.get('compiler_gui'):
        try:
            user_code = get_user_input()
            run_compiler(user_code, capture_output=False)
        except Exception as e:
            print("Error:", e)
            sys.exit(1)