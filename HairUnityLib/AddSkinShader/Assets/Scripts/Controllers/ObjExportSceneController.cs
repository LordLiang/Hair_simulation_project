using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace SceneController {
	public class ObjExportSceneController : MonoBehaviour
	{

		public MeshFilter meshFilter;
		public string filePath;

		// Use this for initialization
		void Start()
		{
			List<Vector3> vertices;
			List<int> faces;
            List<Vector2> uvs;
            List<Vector3> normals;
			ExportMesh(meshFilter.mesh, out vertices, out faces, out uvs, out normals);

			if (filePath != null && filePath != "")
			{
				var fileStream = System.IO.File.OpenWrite(filePath);
				var fileWriter = new System.IO.StreamWriter(fileStream);
				foreach (var vertex in vertices)
				{
					fileWriter.WriteLine("v {0} {1} {2}", vertex.x, vertex.y, vertex.z);
				}
                foreach (var uv in uvs) {
                    fileWriter.WriteLine("vt {0} {1}", uv.x, uv.y);
                }
                foreach (var normal in normals) {
                    fileWriter.WriteLine("vn {0} {1} {2}", normal.x, normal.y, normal.z);
                }
				for (int i = 0; i < faces.Count; i += 3)
				{
                    fileWriter.WriteLine("f {0}/{0}/{0} {1}/{1}/{1} {2}/{2}/{2}", faces[i], faces[i + 1], faces[i + 2]);
				}

				fileWriter.Close();
			}

            Debug.Log("Mesh writed");
		}

        void ExportMesh(Mesh mesh, out List<Vector3> vertices, out List<int> faces, out List<Vector2> uvs, out List<Vector3> normals)
		{
			var tmpVertices = mesh.vertices;
			var tmpFaces = mesh.triangles;
            var tmpUvs = mesh.uv;
            var tmpNormals = mesh.normals;

			var bounds = mesh.bounds;
			for (int i = 0; i < tmpVertices.Length; ++i)
				tmpVertices[i] -= bounds.center;

			vertices = new List<Vector3>();
			faces = new List<int>();
            normals = new List<Vector3>();
            uvs = new List<Vector2>();

            Dictionary<Vector3, int> reIndexDict = new Dictionary<Vector3, int>();
            int idx = 1;
            for (int i = 0; i < tmpVertices.Length; ++i)
            {
                         if (!reIndexDict.ContainsKey(tmpVertices[i]))
                         {
                             reIndexDict.Add(tmpVertices[i], idx++);
                             vertices.Add(tmpVertices[i]);
                             uvs.Add(tmpUvs[i]);
                             normals.Add(tmpNormals[i]);
            	}
            }

            foreach (var vertexIdx in tmpFaces)
            faces.Add(reIndexDict[tmpVertices[vertexIdx]]);

		}
	}

}