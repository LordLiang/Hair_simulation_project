* *matrix idx is line priority*.

# Header (hair geometry) --- 4+4+4 = 12 bytes
* **Int a:** number of hair particles
* **Int b:** number of hair strands
* **Int c:** number of hair particles per strand

# Header2 (dynamic) --- 4+4+120 = 128 bytes
* **Int m:** number of guidance/group
* **Int n:** number of frame
* **Char[120] s:** the original mcx

# Reconstruction Information, \*.recons

* **Header** --- 12 bytes
* **Header2** --- 128 bytes
* **Index** --- 12 bytes
  * **Int:** Guide Hair start
  * **Int:** Initial Frame start
  * **Int:** Weights start
* **Flags** --- 12 bytes
  * **Int:** group start?
  * **Int:** neighboring start?
  * **Int:** Interpolation start?
* **Guide Hairs** --- 4m+24mc+n(4+64+48mc) bytes
  * **For Loop** x m
    * **Int:** guide hair ID
  * **For Loop** x m x c
    * **Float** x 3: guide static position
  * **For Loop** x m x c  
    * **Float** x 3: guide static direction
  * **For Loop** x n  
    * **Int:** Frame ID
    * **Float** x 16: rigid head motion
    * **For Loop** x m x c
      * **Float** x (9+3): rot, translate
* **Initial Frame**  --- 24a bytes
  * **For Loop** x a
    * **Float** x 3: static position
  * **For Loop** x a  
    * **Float** x 3: static direction
* **Weights** --- dynamic
  * **Int:** number of bytes in this section (include itself)
  * **For Loop** x b
    * **Int p:** number of guides  
    * **For Loop** x p
      * **Int:** guide ID (global overall ID)
    * **For Loop** x p
      * **Float:** guide weight
* **Group (Optional)** --- 4b bytes
  * **For Loop** x b
    * **Int:** group ID
* **Neighboring (Optional)** --- dynamic
  * **For Loop** x m  
    * **Int q:**: number of neigh (including itself)
    * **Int** x q: neigh group ID
* **Interpolation (Optional)** --- dynamic
  * **Char[128]:** relative path of anim2, '0' means none
*
