# 🤖 AI Gesture Controller

An AI-powered Gesture Controller that allows users to control their computer using hand gestures captured through a webcam. The project leverages Computer Vision and Artificial Intelligence to provide a touch-free Human-Computer Interaction (HCI) experience.

## 🚀 Features

- 🖱️ Virtual Mouse Control
  - Cursor Movement
  - Left Click
  - Right Click
  - Double Click
  - Drag & Drop

- 🎮 Gaming Mode
  - Gesture-based keyboard controls
  - Move Left / Right
  - Jump
  - Shoot
  - Reload

- 🎵 Music Control
  - Play / Pause
  - Next Track
  - Previous Track
  - Volume Control

- 🔊 Volume Control

- 💡 Brightness Control

- 📜 Scroll Control

- 📸 Screenshot Capture

- ✋ Real-Time Hand Tracking

---

## 🛠️ Tech Stack

- Python
- OpenCV
- MediaPipe
- NumPy
- PyAutoGUI
- Pycaw
- screen-brightness-control

---

## 🧠 How It Works

1. Webcam captures live video.
2. MediaPipe detects 21 hand landmarks.
3. OpenCV processes each frame.
4. Gestures are recognized based on finger positions.
5. The detected gesture is mapped to a predefined computer action.
6. PyAutoGUI and other libraries execute the corresponding action.

---

## 📂 Project Structure

```
AI-Gesture-Controller/
│
├── main.py
├── modes/
│   ├── mouse_mode.py
│   ├── gaming_mode.py
│   ├── music_mode.py
│   ├── volume_mode.py
│   
│
├── utils/
├── assets/
├── requirements.txt
└── README.md
```

---

## 🎯 Applications

- Touchless Computer Control
- Gaming
- Smart Presentations
- Accessibility
- Smart Home Systems
- Interactive Learning
- Healthcare

---

## 🔮 Future Improvements

- Voice + Gesture Control
- Custom Gesture Training
- Face Recognition Login
- Multi-Hand Detection
- AI Gesture Personalization
- Cross-Platform Support

---

## 👨‍💻 Author

**Harsh Kumar**

Computer Science Engineering Student | KIIT University
