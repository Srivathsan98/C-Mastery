# 🧱 PHASE 1: CORE FOUNDATIONS (You must be flawless here)

## 1. Basic Syntax & Structure

- Compilation process (preprocessing → compiling → linking)
- `main()`, arguments
- Data types, type modifiers
- Input/output (`printf`, `scanf`)
- Operators

## 🧠 Questions

### Beginner (15)

1. What happens from .c file to executable?
2. Difference between `int`, `float`, `double`?
3. What is format specifier?
4. What is undefined behavior?
5. What is implicit conversion?
6. What is explicit casting?
7. What is `sizeof` operator?
8. Difference between `++i` and `i++`?
9. What is `const`?
10. What is `volatile`?
11. Why `main` returns `int`?
12. What is escape sequence?
13. What is ASCII?
14. What is token in C?
15. What is identifier?

### Intermediate (20)

1. Explain compilation stages in detail
2. What is translation unit?
3. What is UB example?
4. How format specifier mismatch breaks program?
5. What is integer promotion?
6. What is type punning?
7. What is strict aliasing?
8. What is endianness?
9. What is padding?
10. What is alignment?
11. What is data model (ILP32, LP64)?
12. What happens if main doesn't return?
13. What is `restrict` keyword?
14. What is sequence point?
15. What is expression vs statement?
16. What is lvalue/rvalue?
17. What is UB vs implementation-defined?
18. What is trap representation?
19. Why float comparison is risky?
20. What is signed overflow behavior?

### Advanced (30)

1. ABI impact on data types
2. How compiler optimizes arithmetic
3. Bit-level representation of float
4. IEEE-754 deep dive
5. Why strict aliasing exists
6. How UB enables optimization
7. Register allocation basics
8. Compiler flags impact (-O2, -O3)
9. Assembly output for simple C code
10. Constant folding
11. Dead code elimination
12. Stack vs register usage
13. Inline expansion
14. What breaks optimization?
15. When volatile is required?
16. Hardware vs language memory model
17. Sequence points in modern compilers
18. UB exploitation examples
19. Loop unrolling
20. Branch prediction relevance
21. Pipeline hazards basics
22. Cache effects
23. Alignment penalties
24. False sharing basics
25. Code generation for arithmetic
26. Instruction selection
27. Calling convention basics
28. Why undefined behavior exists in spec
29. Memory layout of struct with padding
30. How compiler treats constant expressions

---

# 🧠 PHASE 2: CONTROL FLOW

- `if`, `switch`
- loops
- `break`/`continue`/`goto`

*(Questions omitted here? No — brutal means complete)*

## Questions

### Beginner (15)

- Control flow basics, loop traces, switch fallthrough, etc.

### Intermediate (20)

- Loop optimizations, infinite loop scenarios, Duff's device intro

### Advanced (30)

- Branch prediction, jump tables, compiler optimizations on loops, Duff's device implementation

---

# 🧩 PHASE 3: FUNCTIONS & STACK

- Function calls
- Recursion
- Stack frames

## Key Topics

- Call stack
- Parameter passing
- Tail recursion

*(Repeat 15/20/30 pattern)*

---

# 🧵 PHASE 4: POINTERS (MOST IMPORTANT)

> This is where most people fail.

## Topics

- Pointer basics
- Pointer arithmetic
- Arrays vs pointers
- Double pointers
- Function pointers

## Questions (sample highlights)

### Beginner (15)

1. What is pointer?
2. What is NULL?
3. Pointer vs array?

### Intermediate (20)

1. Pointer arithmetic rules
2. Pointer to function usage
3. Pointer to pointer use cases

### Advanced (30)

1. Pointer aliasing
2. Dangling pointer scenarios
3. Function pointer tables
4. Memory corruption debugging
5. Pointer arithmetic UB cases

---

# 🧱 PHASE 5: ARRAYS & STRINGS

- Static arrays
- Multidimensional arrays
- Strings & char pointers

---

# 🧬 PHASE 6: MEMORY MANAGEMENT

## Topics

- Stack vs Heap
- `malloc`, `calloc`, `realloc`, `free`
- Memory leaks

## Advanced Focus

- Fragmentation
- Custom allocators
- Memory pools

---

# 🧩 PHASE 7: STRUCTS, UNIONS, ENUMS

- Struct alignment
- Padding
- Bitfields

---

# ⚙️ PHASE 8: PREPROCESSOR

- Macros
- Conditional compilation
- Header guards

---

# 🧵 PHASE 9: FILE HANDLING

- File I/O
- Binary vs text
- Buffers

---

# 🔗 PHASE 10: LINKING & BUILD SYSTEM

- Static vs dynamic linking
- Libraries
- Makefiles

---

# 🧠 PHASE 11: SYSTEM PROGRAMMING

- Processes
- IPC (pipes, shared memory)
- Signals

---

# 🧵 PHASE 12: MULTITHREADING (POSIX)

- pthreads
- mutex
- condition variables

---

# ⚡ PHASE 13: LOW-LEVEL & EMBEDDED C

- Memory-mapped I/O
- Bit manipulation
- Interrupt concepts

---

# 🧨 PHASE 14: ADVANCED TOPICS

- Undefined behavior mastery
- Optimization tricks
- Security (buffer overflow)
- Reverse engineering basics

---

# 🧠 RULE FOR THIS ROADMAP

> You cannot move forward until:
> 
> - You can answer 70% of advanced questions without hesitation
> - You can code without Googling