using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class MyMath {
    //transform 0.01~100.0 to 0.0~1.0
    public static float Pow100ToNormalized(float pow100) {
        return Mathf.Log10(pow100) / 4.0f + 0.5f;
    }

    //transform 0.0~1.0 to 0.01~100.0
    public static float NormalizedToPow100(float num) {
        return Mathf.Pow(10.0f, (num - 0.5f) * 4);
    }

    public static Matrix4x4 MatrixInterpolation(Matrix4x4 a, Matrix4x4 b, float p)
    {
        //ret = a * p + b * (1 - p)
        Matrix4x4 ret = Matrix4x4.identity;
        for (int i = 0; i < 4; ++i)
            for (int j = 0; j < 4; ++j)
                ret[i, j] = a[i, j] * p + b[i, j] * (1 - p);
        return ret;
    }

    public static void TransformFromMatrix(Matrix4x4 matrix, Transform trans)
    {
        //trans.rotation = QuaternionFromMatrix(matrix);
        //trans.position = matrix.GetColumn(3); // uses implicit conversion from Vector4 to Vector3
        trans.localRotation = ExtractRotation(matrix);
        trans.localPosition = ExtractPosition(matrix);
        trans.localScale = ExtractScale(matrix);
    }

    public static Quaternion QuaternionFromMatrix(Matrix4x4 m)
    {
        // Adapted from: http://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/index.htm
        Quaternion q = new Quaternion();
        q.w = Mathf.Sqrt(Mathf.Max(0, 1 + m[0, 0] + m[1, 1] + m[2, 2])) / 2;
        q.x = Mathf.Sqrt(Mathf.Max(0, 1 + m[0, 0] - m[1, 1] - m[2, 2])) / 2;
        q.y = Mathf.Sqrt(Mathf.Max(0, 1 - m[0, 0] + m[1, 1] - m[2, 2])) / 2;
        q.z = Mathf.Sqrt(Mathf.Max(0, 1 - m[0, 0] - m[1, 1] + m[2, 2])) / 2;
        q.x = Mathf.Sign(q.x * (m[2, 1] - m[1, 2]));
        q.y = Mathf.Sign(q.y * (m[0, 2] - m[2, 0]));
        q.z = Mathf.Sign(q.z * (m[1, 0] - m[0, 1]));
        return q;
    }

    
    public static Quaternion ExtractRotation(Matrix4x4 matrix)
    {
        Vector3 forward;
        forward.x = matrix.m02;
        forward.y = matrix.m12;
        forward.z = matrix.m22;

        Vector3 upwards;
        upwards.x = matrix.m01;
        upwards.y = matrix.m11;
        upwards.z = matrix.m21;

        return Quaternion.LookRotation(forward, upwards);
    }

    public static Vector3 ExtractPosition(Matrix4x4 matrix)
    {
        Vector3 position;
        position.x = matrix.m03;
        position.y = matrix.m13;
        position.z = matrix.m23;
        return position;
    }

    public static Vector3 ExtractScale(Matrix4x4 matrix)
    {
        Vector3 scale;
        scale.x = new Vector4(matrix.m00, matrix.m10, matrix.m20, matrix.m30).magnitude;
        scale.y = new Vector4(matrix.m01, matrix.m11, matrix.m21, matrix.m31).magnitude;
        scale.z = new Vector4(matrix.m02, matrix.m12, matrix.m22, matrix.m32).magnitude;
        return scale;
    }
}