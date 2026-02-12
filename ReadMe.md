# DSL for Laboratory Data Analysis

**Course:** Principles of Compiler Design  
**Semester:** Fall 1404 (Winter 2026)  

**Team Members:**  
*   Mohammad Ali Ahmadian
*   Ali Jabbaripour
*   Seyed Ahmed Mousavi Malvajerdi

---

## Project Description
This project implements a Domain-Specific Language (DSL) designed to simplify laboratory data analysis. It allows users to write high-level commands in **Natural Persian** or **English** to manipulate datasets, removing the need to write raw Python code manually.

The compiler translates these commands into executable Python scripts that utilize `pandas` for data processing and `matplotlib` for visualization.

## Technical Architecture
The compiler follows a 4-stage pipeline:
1.  **Pre-processing:** Regex-based translation of natural language to Intermediate Representation (IR).
2.  **Parsing:** Uses **Lark** to generate an Abstract Syntax Tree (AST) from the IR.
3.  **Code Generation:** Traverses the AST to produce valid Python code.
4.  **Execution:** Runs the generated script to output charts (`.png`) and reports.

## Features
*   **Data Input:** Support for CSV, Excel, and JSON files.
*   **Cleaning:** Automatic handling of missing values and **IQR-based outlier removal**.
*   **Analysis:** Filtering, sorting, grouping, and statistical calculations.
*   **Visualization:** Automates creation of Histograms, Scatter plots, and Box plots.

## Installation

  **Install dependencies:**
```bash
pip install pandas matplotlib seaborn lark-parser
```
2. **Run the compiler:**
```bash
python main.py input.txt
```