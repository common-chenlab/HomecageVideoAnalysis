""" use this python file to include direct paths to folder paths and models used """


# folder path to complete, error, and mat folder for TM and CV-
folder_paths = {}

# path to move any errors caught/exceptions (training module)
folder_paths['errortm'] = r'Z:\Projects\Homecage\DLCVideos\trainingmodule_errors'

# path to save generated .MAT files (training module)
folder_paths['matfiletm'] = r'Z:\Projects\Homecage\DLCVideos\trainingmodule_matfiles'

# path to move any errors caught/exceptions (cageview)
folder_paths['errorcv'] = r'Z:\Projects\Homecage\DLC\Other\cageview_errors'

# path to save generated .MAT files (cageview)
folder_paths['matfilecv'] = r'Z:\Projects\Homecage\DLC\Other\cageview_matfiles'


# paths to different deep learning models used in analysis
modelinfo = {}

# path to custom trained OCR LSTM model
modelinfo['ocr'] = r'Z:\Projects\Homecage\DLC\VAModels\OCR\best_lstm_model/'

# deeplabcut information for training module
modelinfo['dlctm'] = {
                        'model_paths': 
                            {
                            'black': r'Z:\Projects\Homecage\DLC\VAModels\DLC\trainingmodule\blackcoat\trainingmodule_black_v6-chenlab-2023-04-25\exported-models\DLC_trainingmodule_black_v6_mobilenet_v2_1.0_iteration-0_shuffle-1', 
                            'white': r'Z:\Projects\Homecage\DLC\VAModels\DLC\trainingmodule\whitecoat\trainingmodule_v4_white-chenlab-2022-05-04_eval\exported-models\DLC_trainingmodule_v4_white_mobilenet_v2_0.35_iteration-0_shuffle-1',
                            },
                        'body_parts': ['nose', 'leftear', 'rightear', 'neck', 'upperback', 'lowerback', 'tail', 'tail2', 'fl_foot', 'fr_foot', 'bl_foot', 'br_foot']
                }

# deeplabcut information for cage view
modelinfo['dlccv'] = { 
                        'model_paths':
                            {
                            'blackwhite': r'Z:\Projects\Homecage\DLC\VAModels\DLC\cageview\blackwhite\cageview_v3_blackmice_white-chenlab-2022-06-27\exported-models\DLC_cageview_v3_blackmice_white_mobilenet_v2_1.0_iteration-0_shuffle-1',
                            'whitewhite': r'Z:\Projects\Homecage\DLC\VAModels\DLC\cageview\whitewhite\cageview_v3_whitemice_white-chenlab-2022-06-27\exported-models\DLC_cageview_v3_whitemice_white_mobilenet_v2_1.0_iteration-0_shuffle-1',
                            'blackred': r'Z:\Projects\Homecage\DLC\VAModels\DLC\cageview\blackred\cageview_v3_blackmice_red-chenlab-2022-06-27\exported-models\DLC_cageview_v3_blackmice_red_mobilenet_v2_1.0_iteration-0_shuffle-1',
                            'whitered':  r'Z:\Projects\Homecage\DLC\VAModels\DLC\cageview\whitered\cageview_v3_whitemice_red-chenlab-2022-06-27\exported-models\DLC_cageview_v3_whitemice_red_mobilenet_v2_1.0_iteration-0_shuffle-1',
                            },
                        'body_parts': ['nose', 'head', 'neck', 'upperback', 'lowerback', 'tail', 'tail2']

                }

# path to coat recognition model
modelinfo['coatrecognition'] = r'Z:\Projects\Homecage\DLC\VAModels\ImageClassification\trainingmodule\coatcolorclassifier\coat_classifier_weights_v8.h5'

# # path to maskrcnn training module model
# modelinfo['maskrcnntm'] = r'Z:\Projects\Homecage\DLC\VAModels\Segmentation\trainingmodule\tm_detect_03282022.h5'
modelinfo['tmdetection'] = r'Z:\Projects\Homecage\DLC\VAModels\DLC\tm-outline\tm-outline_mobilenet_v2_1.0_VERSION_2'

# path to maskrcnn cage view model
modelinfo['maskrcnncv'] = r'Z:\Projects\Homecage\DLC\VAModels\Segmentation\cageview\mask_rcnn_cage_ls_06132022.h5'


# path to led object detection model
modelinfo['objdetectLED'] = {
                                'model_folder_path': r'Z:\Projects\Homecage\DLC\VAModels\ObjectDetection\led\102622_yolov7',
                                'weights': 'yolov7_training_20000.weights',
                                'config': 'yolov7_training.cfg',
                                'trained_image_size': (416, 416),
                                'channels': 1
                        }

# location for sensitive information
sensitive_information_folder = r'Z:\Projects\Homecage\DLC\SensitiveInformation'


led_issue_info = {
    # list of rigs that had LED issues (rig numbers should be integers)
    'rig_led_issues': [11, 14, 25],

    # path to csv files for each rig with led issues
    'led_issue_csv_paths': {
                            11: r'Z:\Projects\Homecage\DLC\VAModels\LedIssueFiles\rig_11_trial_dt.csv',
                            14: r'Z:\Projects\Homecage\DLC\VAModels\LedIssueFiles\rig_14_trial_dt.csv',
                            25: r'Z:\Projects\Homecage\DLC\VAModels\LedIssueFiles\rig_25_trial_dt.csv'
                        }
    }
