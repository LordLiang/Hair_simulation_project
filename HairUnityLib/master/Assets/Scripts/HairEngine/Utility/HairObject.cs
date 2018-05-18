using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEngine;

namespace HairEngine {
    namespace Utility {
        //hairObject is the representation of hair in Unity
        //because the limitation of Unity that each mesh filter can only contain 60000+ points
        //so we add SubHair game object to hold the "real" vertices while HairObject is acting like a container of all the SubHair game object
        public class HairObject: MonoBehaviour {
            
            public enum HairColorStyle {
                Fixed = 0 //show the hair in rainbow color
            }

            private int strandCount = 0;
            public int StrandCount { get { return strandCount; } }
            private int particleCount = 0;
            public int ParticleCount { 
                get {
                    //for we duplicate the first and last particle for each strand for rendering
                    return particleCount - strandCount * 2;
                } 
            }  
            private HashSet<int> hairEndParticleSet = new HashSet<int>(); //the particle root index of each strand
            private Material hairMaterial = null;
            private List<int> particleAssignmentMap = new List<int>(); //indicates whether the scanning cursor should move on when doing assignment, the first "virtual" particle of strand and the "last" real particle of strand should be 0, otherwise it will be 1

			private float currentHairRadius = 0.001f;

			public float CurrentHairRadius
            {
                get { return currentHairRadius; }
                set
                {
                    currentHairRadius = value;
                    hairMaterial.SetFloat("_R", currentHairRadius);
                }
            }

            private Color hairColor = new Color(62.0f / 255.0f, 45.0f / 255.0f, 41.0f / 255.0f);
            public Color HairColor {
                get { return hairColor; }
            }

            private float hairColorHNoise = 0.0f;
            private float hairColorSNoise = 0.0f;
            private float hairColorVNoise = 0.17f;

            [Range(0.0f, 0.5f)]
            public float iHairColorHNoise = 0.0f;
            [Range(0.0f, 0.5f)]
            public float iHairColorSNoise = 0.0f;
            [Range(0.0f, 0.5f)]
            public float iHairColorVNoise = 0.17f;
            public Color iHairColor = new Color(62.0f / 255.0f, 45.0f / 255.0f, 41.0f / 255.0f);

            private void UpdateFixedColorIfNeeded() {
                if (Mathf.Abs(iHairColorHNoise - hairColorHNoise) > 1e-6f
                    || Mathf.Abs(iHairColorSNoise - hairColorSNoise) > 1e-6f
                    || Mathf.Abs(iHairColorVNoise - hairColorVNoise) > 1e-6f
                    || hairColor.GetHashCode() != iHairColor.GetHashCode()) {

                    hairColorHNoise = iHairColorHNoise;
                    hairColorVNoise = iHairColorVNoise;
                    hairColorSNoise = iHairColorSNoise;
                    hairColor = iHairColor;

                    SetHairRepresentationStyleToFixedColor();
                }
            }

            public static GameObject CreateGameObject() {
                var gameObject = new GameObject();
                gameObject.AddComponent<HairObject>();
                gameObject.name = "Hair";
                return gameObject;
            }

            private void Awake()
            {
                hairMaterial = new Material(Shader.Find("Custom/HairStrand"));
                hairMaterial.SetFloat("_R", currentHairRadius);
            }

            private void Update()
            {
                UpdateFixedColorIfNeeded();
            }

            //when we append a SubHair Object, we currently not only append one hair strand
            //so we use List<Vector3[]>, every element of particlesGroups represents a hair strand
            //to represent a hair as a B spline curve, we use different strategies, we use normal to store the next particle's position if exsits
            //and line indices have been made to every other particles instead of the last three particles
            public void AppendSubHair(List<Vector3[]> particlesGroup, ColorApplierDelegate colorApplier) {
                var subHairObject = new GameObject();

                subHairObject.AddComponent<HairIndexer>();
                subHairObject.AddComponent<MeshFilter>();
                subHairObject.AddComponent<MeshRenderer>();
                subHairObject.transform.parent = this.transform;
                subHairObject.name = "subhair";

                //sum up the total particles and allocate the space
                int subHairParticleCount = 0;
                int subHairStrandCount = 0;
                foreach (var particles in particlesGroup)
                {
                    subHairParticleCount += particles.Length;
                    subHairStrandCount += 1;
                }

                subHairParticleCount += subHairStrandCount * 2; //we add two additional particle for the strand root and end to enable the first and last segment's rendering

                var vertices = new Vector3[subHairParticleCount];
                var normals = new Vector3[subHairParticleCount];
                var colors_ = new Color[subHairParticleCount];
                var indices = new int[2 * (subHairParticleCount - 3 * subHairStrandCount)]; // the last three particles have no indices, every line has two indices

                int pi = 0, ii = 0; //pi denotes current scanning particle index(ie. normals, colors_ index), ii denotes current indices scanning index
                foreach (var particles in particlesGroup)
                {
                    //add to particle root set
                    hairEndParticleSet.Add(pi + particleCount);

                    var currentStrandColor = colorApplier();
                    for (int i = -1; i < particles.Length + 1;) 
                    {
                        particleAssignmentMap.Add((i < 0 || i == particles.Length - 1) ? 0 : 1);
                        vertices[pi] = particles[Math.Max(Math.Min(i, particles.Length - 1), 0)];

                        if (i != -1) //changed
                            normals[pi - 1] = vertices[pi];
                        colors_[pi] = currentStrandColor; //default white

                        if (i < particles.Length - 2) //changed
                        {
                            indices[ii] = pi;
                            indices[ii + 1] = pi + 2;
                            ii += 2;
                        }
                        ++i; ++pi;
                    }
                }

                //assign vertices, normals, colors_ and indices to SubHair object
                var mesh = subHairObject.GetComponent<MeshFilter>().mesh;
                mesh.vertices = vertices;
                mesh.normals = normals;
                mesh.colors = colors_;
                mesh.SetIndices(indices, MeshTopology.Lines, 0);

                //set the material
                subHairObject.GetComponent<MeshRenderer>().sharedMaterial = hairMaterial;

                //update the strand index, particle index and total particle and strand count
                var indexer = subHairObject.GetComponent<HairIndexer>();
                indexer.particleBeginIndex = particleCount;
                indexer.particleEndIndex = (particleCount += subHairParticleCount);
                indexer.hairBeginIndex = strandCount;
                indexer.hairEndIndex = (strandCount += subHairStrandCount);
            }


            public void SetHairRepresentationStyle(HairColorStyle style) {
                if (style == HairColorStyle.Fixed)
                    SetHairRepresentationStyleToFixedColor();
            }
             
            //set the hair style to rainbow color
            private void SetHairRepresentationStyleToFixedColor() {
                foreach (Transform subhair in this.transform) {
                    var indexer = subhair.GetComponent<HairIndexer>();
                    var mesh = subhair.GetComponent<MeshFilter>().mesh;
                    var colors = mesh.colors;

                    float fixedColorH, fixedColorS, fixedColorV;
                    Color.RGBToHSV(hairColor, out fixedColorH, out fixedColorS, out fixedColorV);

                    var color = new Color();

                    for (int i = indexer.particleBeginIndex; i < indexer.particleEndIndex; ++i) {
                        if (IsHairEndParticle(i)) {
                            var h = UnityEngine.Random.Range(-hairColorHNoise, hairColorHNoise) + fixedColorH;
                            var s = UnityEngine.Random.Range(-hairColorSNoise, hairColorSNoise) + fixedColorS;
                            var v = UnityEngine.Random.Range(-hairColorVNoise, hairColorVNoise) + fixedColorV;
                            color = Color.HSVToRGB(Mathf.Clamp01(h), Mathf.Clamp01(s), Mathf.Clamp01(v));
                        }
                        colors[i - indexer.particleBeginIndex] = color;
                    }

                    mesh.colors = colors;
                }
            }

            private bool IsHairEndParticle(int i) {
                return hairEndParticleSet.Contains(i);
            }

            //since copy vertices is not efficent in Unity
            //when we want to access data in vertices
            //we can get vertices buffer to make a cache
            public Vector3[] GetVerticesBuffer() {
                Vector3[] buffer = new Vector3[particleCount];
                int bufferIdx = 0;
                foreach (Transform subhair in this.transform) {
                    var vertices = subhair.GetComponent<MeshFilter>().mesh.vertices;
                    for (int i = 0; i < vertices.Length; ++i)
                        buffer[bufferIdx++] = vertices[i];
                }
                return buffer;
            }

            public void SetHairPositions(Vector3[] positions)
            {
                if (positions.Length != this.particleCount - this.strandCount * 2) //because we add two additional particle for each strand
                    throw new Exception("positions length is not equal to particle count");

                int pi = 0;
                int totalI = 0;
                foreach (Transform subhair in this.gameObject.transform)
                {
                    //because the spcial shader we use, when we update hair position
                    //we must update the normal too
                    var subhairMesh = subhair.GetComponent<MeshFilter>().mesh;
                    var vertices = new Vector3[subhairMesh.vertexCount];
                    var normals = new Vector3[subhairMesh.vertexCount];
                    for (int i = 0; i < vertices.Length; ++i)
                    {
                        vertices[i] = positions[pi];
                        if (i > 0)
                            normals[i - 1] = positions[pi];
                        
                        pi += particleAssignmentMap[totalI++];
                    }
                    subhairMesh.vertices = vertices;
                    subhairMesh.normals = normals;
                }
            }
        }

        public class HairIndexer : MonoBehaviour
        {
            //end index not include
            public int particleBeginIndex, particleEndIndex;
            public int hairBeginIndex, hairEndIndex; 
            public string hairName;

            HairIndexer() { }
        }

        public delegate Color ColorApplierDelegate();

        public class ColorApplier {
            public static ColorApplierDelegate DefaultApplier = () => UnityEngine.Random.ColorHSV(0.0f, 1.0f);
        }
    }
}