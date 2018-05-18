using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;
using UnityEngine;
using HairEngine.Loader;

namespace HairEngine.Utility
{
    public abstract class HairAnimator
    {
        public abstract void UpdateHair(HairObject hairObject, ref Matrix4x4 transformationMatrix);
        public abstract void Dispose();
        protected int currentFrame = 0;
        public int CurrentFrame { get { return currentFrame;  } }
    }

    public class StaticHairAnimator: HairAnimator
    {
        public StaticHairAnimator() { }

        public override void UpdateHair(HairObject hairObject, ref Matrix4x4 transformationMatrix)
        {
            //Do nothing
            currentFrame += 1;
            if (transformationMatrix != null)
                transformationMatrix = Matrix4x4.identity;
        }

        public override void Dispose()
        {
            //Do nothing
        }
    }

    public class AnimHairAnimator: HairAnimator
    {
        public AnimHairAnimator(String filePath)
        {
            reader = new BinaryReader(File.Open(filePath, System.IO.FileMode.Open));
            strandCount = reader.ReadInt32();
            particleCount = reader.ReadInt32();
            particlePerStrand = new int[strandCount]; 
            for (int i = 0; i < strandCount; ++i)
                particlePerStrand[i] = reader.ReadInt32();

            buffer = new Vector3[particleCount];

            startPos = reader.BaseStream.Position;
        }

        public GameObject CreateHairObject()
        {
            if (reader.BaseStream.Position != startPos)
                reader.BaseStream.Seek(startPos, SeekOrigin.Begin);
            for (int i = 0; i < 16; ++i)
                reader.ReadSingle();
            var vertices = new Vector3[particleCount];
            for (int i = 0; i < particleCount; ++i)
                vertices[i] = new Vector3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
            return HairLoader.Load(vertices, strandCount, (i) => particlePerStrand[i]);
        }

        public override void UpdateHair(HairObject hairObject, ref Matrix4x4 transformationMatrix)
        {
            if (this.particleCount != hairObject.ParticleCount)
                throw new Exception("Hairobject incorrect");

            if (reader.PeekChar() < 0)
            {
                reader.BaseStream.Seek(startPos, SeekOrigin.Begin);
                currentFrame = 0;
            }

            currentFrame += 1;

            //update the transformation matrix
            if (transformationMatrix != null)
                for (int i = 0; i < 4; ++i)
                    for (int j = 0; j < 4; ++j)
                        transformationMatrix[i, j] = reader.ReadSingle();

            //update the positions
            for (int i = 0; i < particleCount; ++i)
                buffer[i] = new Vector3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
            hairObject.SetHairPositions(buffer);
        }

        public override void Dispose()
        {
            reader.Close();
        }

        private BinaryReader reader;
        private int strandCount;
        private int particleCount;
        private int[] particlePerStrand;
        private Vector3[] buffer;

        private long startPos;
    }
}
