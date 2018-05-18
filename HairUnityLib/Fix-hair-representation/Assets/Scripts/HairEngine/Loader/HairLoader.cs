using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using HairEngine.Utility;

namespace HairEngine {
    namespace Loader{
		public class HairLoader
		{
			public delegate int NumberOfParticleAtStrandAtIndex(int index);

            public static GameObject Load(Vector3[] particles, int strandCount, NumberOfParticleAtStrandAtIndex numberOfParticleAtStrandAtIndex, ColorApplierDelegate colorApplier = null, int limit = 60000, string hairName = "unknown")
			{
                if (colorApplier == null)
                    colorApplier = ColorApplier.DefaultApplier;

                var gameObject = HairObject.CreateGameObject();
                var hairObject = gameObject.GetComponent<HairObject>();

                var particlesGroup = new List<Vector3[]>();
                //i denotes current strand scanning index
                //pi denotes current particle scanning index
                //totalParticle denotes how many particles have been scanned in current sub hair
                for (int i = 0, pi = 0, totalParticle = 0; i < strandCount; ++i) {
                    int currentStrandParticleCount = numberOfParticleAtStrandAtIndex(i);

                    var strandParticles = new Vector3[currentStrandParticleCount];
                    for (int j = 0; j < currentStrandParticleCount; ++j)
                        strandParticles[j] = particles[j + pi];
                    particlesGroup.Add(strandParticles);

                    pi += currentStrandParticleCount;

                    if (totalParticle + currentStrandParticleCount > limit || i >= strandCount - 1) {
                        hairObject.AppendSubHair(particlesGroup, colorApplier);
                        particlesGroup.Clear();
                        totalParticle = 0;
                    }
                    totalParticle += currentStrandParticleCount;
                }

                hairObject.SetHairRepresentationStyle(HairObject.HairColorStyle.Rainbow);

                return gameObject;
				//List<GameObject> ret = new List<GameObject>();
				//Color color = colorApply();

				//for (int i = 0, pointCur = 0, groupIdx = 0; i < strandCount;)
				//{
				//	//i indicates the current lines we are scanning
				//	//pointCur indicates the current point cusor we are scanning
				//	//groupIdx indicates the how many group we have scanned
				//	//iEnd indicates the group hair strand is in [i, iEnd)
				//	//totalPoints indicates the total 
				//	int iEnd = i;
				//	int totalPoints = 0;
				//	while (iEnd < strandCount && totalPoints + numberOfParticleAtStrandAtIndex(iEnd) < limit)
				//		totalPoints += numberOfParticleAtStrandAtIndex(iEnd++);

				//	//this time create a group hair object
				//	var hairObject = CreateHairObject(hairName);
				//	//when creating the group and the color apply frequency is EVERY_GROUP
				//	//get the color 
				//	++groupIdx;

				//	var hairObjectIndexer = hairObject.GetComponent<HairIndexer>();
				//	hairObjectIndexer.hairBeginIndex = i;
				//	hairObjectIndexer.particleBeginIndex = pointCur;
				//	hairObjectIndexer.hairEndIndex = iEnd;
				//	hairObjectIndexer.particleEndIndex = pointCur + totalPoints;

				//	var hairObjectMesh = hairObject.GetComponent<MeshFilter>().mesh;

				//	var vertices = new Vector3[totalPoints];
				//	var normals = new Vector3[totalPoints];
				//	var colors = new Color[totalPoints];
				//	var indices = new int[2 * (totalPoints - 3 * (iEnd - i))];

				//	for (int p = pointCur, ic = 0, lc = i, lcPointCur = 0; p < pointCur + totalPoints; ++p)
				//	{
				//		//p indicates the current scanning position in the "points" array, which means p - pointCur is the current position in the "vertices" array
				//		//vc indicates the current vertex position, vc = p - pointCur
				//		//ic indicates the current poistion in the "indices" array
				//		//lc indices the current scanning position in the lines
				//		//lcPointCur indices the current point position in lines[lc]
				//		int vc = p - pointCur;
				//		vertices[vc] = particles[p];
				//		colors[vc] = color;
				//		if (vc > 0)
				//		{
				//			normals[vc - 1] = vertices[vc];
				//		}

				//		//if it is not the last point in the line
				//		if (lcPointCur < numberOfParticleAtStrandAtIndex(lc) - 1)
				//		{
				//			if (lcPointCur < numberOfParticleAtStrandAtIndex(lc) - 3)
				//			{
				//				indices[ic] = vc;
				//				indices[ic + 1] = vc + 2;
				//				ic += 2;
				//			}
				//			++lcPointCur;
				//		}
				//		else
				//		{
				//			++lc;
				//			lcPointCur = 0;
				//			color = colorApply();
				//		}
				//	}

				//	//for (int lc = i, pc = 0, cur = 0; lc < iEnd; ++lc)
				//	//{
				//	//    int size = numberOfParticleAtStrandAtIndex(lc);
				//	//    for (int j = 0; j < size - 3; ++j) {
				//	//        indices[cur] = pc + j;
				//	//        indices[cur + 1] = pc + j + 2;
				//	//        cur += 2;
				//	//    }
				//	//    pc += size;
				//	//}

				//	hairObjectMesh.vertices = vertices;
				//	hairObjectMesh.colors = colors;
				//	hairObjectMesh.SetIndices(indices, MeshTopology.Lines, 0);
				//	hairObjectMesh.RecalculateBounds();
				//	hairObjectMesh.normals = normals;

				//	ret.Add(hairObject);

				//	i = iEnd;
				//	pointCur += totalPoints;
				//}
				//return ret;
			}

			//read file from .hair file
            //int : total particle size
            //total particle size * float* 3: all particle positions
            //int : total strand size
            //total strand size * int : particle size for each strand(use this to get the offset in all particle positions)
            private static GameObject LoadStaticHair(FileStream hairFile, ref HairAnimator animator) {
                animator = new StaticHairAnimator();

                var reader = new BinaryReader(hairFile);
                var particles = new Vector3[reader.ReadInt32()];
                for (int i = 0; i < particles.Length; ++i)
                    particles[i] = new Vector3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
                var strandParticleCounts = new int[reader.ReadInt32()];
                for (int i = 0; i < strandParticleCounts.Length; ++i)
                    strandParticleCounts[i] = reader.ReadInt32();
                reader.Close();

                return HairLoader.Load(particles, strandParticleCounts.Length, (i) => { return strandParticleCounts[i]; } );
            }

            public static GameObject LoadStaticHair(string filePath, ref HairAnimator animator) {
                return HairLoader.LoadStaticHair(File.Open(filePath, FileMode.Open), ref animator);
            }

            public static GameObject LoadAnimationHair(string filePath, ref HairAnimator animator) {
                animator = new AnimHairAnimator(filePath);
                return (animator as AnimHairAnimator).CreateHairObject();
            }
		}
	}
}