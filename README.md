//GROUP NUMBER
//MEMBER NAME: Kephas Tetteh INDEX NUMBER: 4211230210


# ICT411 – Compilers & Translators  
## Mid-Semester Project: ILOC Compiler Front-End  
**Ghana Communication Technology University (GCTU)**  
**Faculty of Computing and Information Systems**  
**Department of Information Technology**  
**Level 400 – BIT**

---

### Project Title  
**411fe – A Simple ILOC Front-End (Scanner, Parser & IR Builder)**

### Group Members
1. Kephas Tetteh – **4211230210**  

> Start Date: Thursday, December 11, 2025  
> Due Date:   Friday, December 26, 2025 (11:59 PM)

---

### Project Overview  
This project implements a compiler front-end named `411fe` that processes a subset of the ILOC assembly language.  
It supports:
- Lexical analysis (scanner) → `-s` flag
- Syntax analysis (parser with error reporting) → `-p` flag
- Intermediate Representation (IR) construction and printing → `-r` flag
- Help menu → `-h` flag

The program is written in **Python 3**.

---

### How to Build & Run  

1. Make sure Python 3 is installed:
   ```bash
   python3 --version
   ```
   
2. Make the launcher script executable:
    ```bash
   chmod +x 411fe
   ```

3. Run the program
    ```bash
    ./411fe -h                  # show help
    ./411fe -s sample.iloc     # scan only
    ./411fe -p sample.iloc       # scan + parse (default mode)
    ./411fe -r sample.iloc     # scan + parse + print IR
    ```