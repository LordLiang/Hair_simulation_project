using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using SFB;
using HairEngine.Loader;
using UnityEngine.UI;
using HairEngine.Utility;

namespace SceneController {
    public class StaticAndAnimationHairViewerController : MonoBehaviour
    {
        private static float MIN_UPDATE_HAIR_TIME = 0.025f;

        //UI Componenet
        public Canvas canvas;
        public Slider scaleSlider;
        public Text scaleValueText;
		public Slider rotationYSlider;
		public Text rotationYValueText;
		public Slider rotationZSlider;
		public Text rotationZValueText;
        public Slider hairRadiusSlider;
        public Text hairRadiusText;
        public GameObject headGameObject;

        public Transform colliderObject;

        public Button selectButton;
        public Button playButton;
        public Button pauseButton;
        public Button stopButton;
        public Button nextButton;
        public Button prevButton;
        public Text currentFrameText;
        private bool isPause = false;

		private GameObject mainHair = null;
        private GameObject MainHair {
            get { return mainHair; }
            set {
                mainHair = value;
                OnTransformationSlider(); //Update hair transformation by slider value
                deltaUpdateHairTime = 1e10f;
            }
        }
        private HairAnimator hairAnimator = null;
        private float deltaUpdateHairTime = 1e10f;

        public bool applyHeadTransformation = false;
        public bool applyColliderTranformation = false;
        public string headTransformationFilePath = "";
        public string colliderWorld2LocalTransformationFilePath = "";

        private bool shouldShowUI = true;

        Matrix4x4[] headTransformationMatrixs = null;
        int currentHeadTranformationIndex = 0;
        Matrix4x4[] colliderLocal2WorldTransformation = null;
        int currentColliderTransformationIndex = 0;

		// Use this for initialization
		void Start()
		{
            MainHair = null;
		}

        void LoadTranformationMatrixs()
        {
            if (applyHeadTransformation)
            {
                headTransformationMatrixs = GetMatrixsFromFile(headTransformationFilePath);
                currentHeadTranformationIndex = 0;
            }
            if (applyColliderTranformation)
            {
                colliderLocal2WorldTransformation = GetMatrixsFromFile(colliderWorld2LocalTransformationFilePath);
                currentColliderTransformationIndex = 0;
                //we load the world2local matrix, so we should inverse all of them
                if (colliderLocal2WorldTransformation != null)
                    for (int i = 0; i < colliderLocal2WorldTransformation.Length; ++i)
                        colliderLocal2WorldTransformation[i] = Matrix4x4.Inverse(colliderLocal2WorldTransformation[i]);
            }
        }

        void Update() 
        {
            OnKeyboard();

            if (!isPause)
                UpdateHair();

            UpdateUI();
        }

        void OnKeyboard()
        {
            if (Input.GetKeyDown(KeyCode.H))
            {
                shouldShowUI = !shouldShowUI;
            }
        }

        void UpdateHair()
        {
            deltaUpdateHairTime += Time.deltaTime;
            if (deltaUpdateHairTime < MIN_UPDATE_HAIR_TIME)
                return;
            else
                deltaUpdateHairTime = 0.0f;
                
            if (mainHair != null)
            {
                Matrix4x4 rigid = Matrix4x4.identity;
                hairAnimator.UpdateHair(mainHair.GetComponent<HairObject>(), ref rigid);
                MyMath.TransformFromMatrix(rigid, headGameObject.transform);

                /*
                if (applyHeadTransformation && headTransformationMatrixs != null && headTransformationMatrixs.Length > 0)
                {
                    MyMath.TransformFromMatrix(headTransformationMatrixs[currentHeadTranformationIndex++], headGameObject.transform);
                    if (currentHeadTranformationIndex >= headTransformationMatrixs.Length)
                        currentHeadTranformationIndex = 0;
                }
                */

                if (applyColliderTranformation && colliderLocal2WorldTransformation != null && colliderLocal2WorldTransformation.Length > 0)
                {
                    MyMath.TransformFromMatrix(colliderLocal2WorldTransformation[currentColliderTransformationIndex++], colliderObject);
                    if (currentColliderTransformationIndex >= colliderLocal2WorldTransformation.Length)
                        currentColliderTransformationIndex = 0;
                }
            }
        }

        void UpdateUI() 
        {
            canvas.gameObject.SetActive(shouldShowUI);
                
            var shouldInteractive = (mainHair != null);

            scaleSlider.interactable = shouldInteractive;
            rotationYSlider.interactable = rotationZSlider.interactable = shouldInteractive;

            if (mainHair != null)
            {
                playButton.gameObject.SetActive(true);
                pauseButton.gameObject.SetActive(true);
                stopButton.gameObject.SetActive(true);
                nextButton.gameObject.SetActive(true);
                prevButton.gameObject.SetActive(true);
                selectButton.gameObject.SetActive(false);
                currentFrameText.gameObject.SetActive(true);
                currentFrameText.text = string.Format("Current Frame: {0}", hairAnimator.CurrentFrame.ToString());

                if (isPause)
                {
                    //pause mode
                    prevButton.enabled = true;
                    nextButton.enabled = true;
                    pauseButton.enabled = false;
                    playButton.enabled = true;
                }
                else
                {
                    //play mode
                    prevButton.enabled = false;
                    nextButton.enabled = false;
                    pauseButton.enabled = true;
                    playButton.enabled = false;
                }

                scaleSlider.value = Mathf.Clamp01(MyMath.Pow100ToNormalized(mainHair.transform.localScale.x));

                var eulerRotaionY = (mainHair.transform.localEulerAngles.y % 360.0f + 360.0f) % 360.0f;//0-360
                var eulerRotaionZ = (mainHair.transform.localEulerAngles.z % 360.0f + 360.0f) % 360.0f;//0-360
                rotationYSlider.value = eulerRotaionY;
                rotationZSlider.value = eulerRotaionZ;
                rotationYValueText.text = eulerRotaionY.ToString();
                rotationZValueText.text = eulerRotaionZ.ToString();

                hairRadiusText.text = hairRadiusSlider.value.ToString();
			}
            else
            {
                playButton.gameObject.SetActive(false);
                pauseButton.gameObject.SetActive(false);
                stopButton.gameObject.SetActive(false);
                nextButton.gameObject.SetActive(false);
                prevButton.gameObject.SetActive(false);
                selectButton.gameObject.SetActive(true);
                currentFrameText.gameObject.SetActive(false);
            }
        }

        public void OnFileButtonSelected()
        {
            var paths = StandaloneFileBrowser.OpenFilePanel("Open Hair Files", "", new[] { new ExtensionFilter("Hair Related File", "hair", "anim") }, false);
            if (paths.Length != 0)
            {
                var path = paths[0].Replace("file://", "");
                if (path.EndsWith("anim"))
                    MainHair = HairLoader.LoadAnimationHair(path, ref hairAnimator);
                else
                    MainHair = HairLoader.LoadStaticHair(path, ref hairAnimator);

                LoadTranformationMatrixs();

                shouldShowUI = false;
            }
        }

        public void OnTransformationSlider()
        {
            if (mainHair != null) {
				mainHair.transform.localScale = new Vector3(
	                MyMath.NormalizedToPow100(scaleSlider.value),
	                MyMath.NormalizedToPow100(scaleSlider.value),
	                MyMath.NormalizedToPow100(scaleSlider.value)
                );
                mainHair.transform.localEulerAngles = new Vector3(mainHair.transform.eulerAngles.x, rotationYSlider.value, rotationZSlider.value);
            }
        }

        public void OnToggleHead()
        {
            headGameObject.SetActive(!headGameObject.activeSelf);
        }

        public void OnSetHairRadius()
        {
            mainHair.GetComponent<HairObject>().CurrentHairRadius = hairRadiusSlider.value;
        }

        public void OnStop()
        {
            Destroy(mainHair.gameObject);
            mainHair = null;
            hairAnimator.Dispose();
            hairAnimator = null;
        }

        public void OnPlay()
        {
            isPause = false;
        }

        public void OnPause()
        {
            isPause = true;
        }

        public void OnNext()
        {
            if (isPause)
            {
                UpdateHair();
            }
        }

        public void OnPrev()
        {

        }

        Matrix4x4[] GetMatrixsFromFile(string filePath)
        {
            if (File.Exists(filePath) == false)
                return null;

            var floatStrs = File.ReadAllText(filePath).Replace("\r\n", "\n").Split();
            if (floatStrs.Length % 16 != 0)
                if (!(floatStrs.Length % 16 == 1 && floatStrs[floatStrs.Length - 1] == ""))
                    throw new System.Exception("file invalid");

            var matrixs = new Matrix4x4[floatStrs.Length / 16];
            for (int i = 0; i < matrixs.Length; ++i)
            {
                matrixs[i] = Matrix4x4.zero;
                for (int j = 0; j < 4; ++j)
                    for (int k = 0; k < 4; ++k)
                        matrixs[i][j, k] = float.Parse(floatStrs[i * 16 + j * 4 + k]);
            }

            return matrixs;
        }
    }
}

