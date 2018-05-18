using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace SceneController
{
    public class AnimationRecordSceneController : MonoBehaviour
    {
        struct CaptureStruct
        {
            public float captureTime;
            public Matrix4x4 headTransformMatrix, colliderWorldToLocalMatrix;
        }

        public Transform headTransform; //the object that take control of the rigid transformation, it will pass to the computation core
        public Transform colliderTransform; //the object of the collider

        bool firstUpdate = true;

        float curUpdateTime, lastUpdateTime, nextTimeToCapture;
        Matrix4x4 lastHeadTransformationMatrix = Matrix4x4.identity;
        Matrix4x4 lastColliderWorldToLocalMatrix = Matrix4x4.identity;
        const float captureTimeStep = 0.03f;

        List<CaptureStruct> captureList = new List<CaptureStruct>();

        // Use this for initialization
        void Start()
        {
            headTransform.gameObject.AddComponent<SimpleSmoothMouseLook>();
            var mouseLook = headTransform.gameObject.GetComponent<SimpleSmoothMouseLook>();
            mouseLook.sensitivity = new Vector2(-6.0f, -6.0f);
        }

        // Update is called once per frame
        void Update()
        {
            if (firstUpdate)
            {
                //force to update current matrix
                curUpdateTime = nextTimeToCapture = 0.0f;
                lastUpdateTime = -1e10f;
                OnCaptureTransformation();

                curUpdateTime = lastUpdateTime = 0.0f;
                nextTimeToCapture = captureTimeStep;

                firstUpdate = false;
            }
            else
            {
                curUpdateTime += Time.deltaTime;
                if (nextTimeToCapture <= curUpdateTime)
                {
                    OnCaptureTransformation();
                    while (nextTimeToCapture <= curUpdateTime)
                        nextTimeToCapture += captureTimeStep;
                }
            }

            lastUpdateTime = curUpdateTime;
            lastHeadTransformationMatrix = headTransform.localToWorldMatrix;
            lastColliderWorldToLocalMatrix = colliderTransform.worldToLocalMatrix;
        }

        void OnCaptureTransformation()
        {
            float p = curUpdateTime - nextTimeToCapture;
            CaptureStruct ret = new CaptureStruct();

            ret.captureTime = nextTimeToCapture;
            ret.headTransformMatrix = MyMath.MatrixInterpolation(lastHeadTransformationMatrix, headTransform.localToWorldMatrix, p);
            ret.colliderWorldToLocalMatrix = MyMath.MatrixInterpolation(lastColliderWorldToLocalMatrix, colliderTransform.worldToLocalMatrix, p);

            captureList.Add(ret);
        }

        public void OnWriteToFile()
        {
            var headTranformationFileWriter = new System.IO.StreamWriter("/Users/vivi/Desktop/motion1/head_trans.txt");
            var colliderTransformationFileWriter = new System.IO.StreamWriter("/Users/vivi/Desktop/motion1/collider_world2local.txt");

            foreach (var capture in captureList)
            {
                for (int i = 0; i < 4; ++i)
                    for (int j = 0; j < 4; ++j)
                    {
                        headTranformationFileWriter.Write(capture.headTransformMatrix[i, j].ToString() + " ");
                        colliderTransformationFileWriter.Write(capture.colliderWorldToLocalMatrix[i, j].ToString() + " ");
                    }
            }

            headTranformationFileWriter.Close();
            colliderTransformationFileWriter.Close();
        }
    }
}