# Guide Hairs, \*.guide, \*.info

int a: number of guide strand  
int a1: particle per strand   
int b: number of frame  
int \* a: guide id  
int: frame id  
float \* a \* a1 \* (9+3): rot, translate  

---

# Weights, \*.weights (deprecated)

int b: number of strand  

For Loop \* b  
* int: number of guides  
* int:   guide Id
* float:   guide weight

---

# Ground Truth, \*.anim

int a: frame number  
int b: particle number  

For Loop \* a  
int: frame id
* **For Loop** \* b  
* float \* 3: position

---

# Ground Truth, \*.anim2

* INT a: frame number  
* INT b: particle number  
* **For Loop** \* a  
  * INT: frame id
  * FLOAT * 16: rigid motion
  * **For Loop** \* b  
    * FLOAT \* 3: position
  * **For Loop** \* b  
    * FLOAT \* 3: direction

---

# Neighbour Map, \*.neigh

* *INT* a: group number  
* **For Loop** \* a  
  * *INT* b: number of neigh, including itself
  * *INT* \* b: neigh group id

---

# Group Info, \*.group

* *INT* a: number of hair strand
* *INT* \* a: the id of each group

---

# Strand Edge Info, \*.bg

* **INT** a: number of Edge
* **INT** : max weight of edge
* **For Loop** \* a  
  * **INT** : id0
  * **INT** : id1 (bigger)
  * **INT** : weight

---

# Interpolation
