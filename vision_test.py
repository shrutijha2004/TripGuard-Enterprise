import cv2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VisionTest")

def test_camera():
    logger.info("Initializing camera hardware check via vision_test.py...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        logger.warning("Camera index 0 failed. Trying index 1...")
        cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        logger.error("❌ ERROR: Could not access any webcam. Check system permissions.")
        return

    logger.info("✅ SUCCESS: Camera initialized successfully! Press 'q' to close test window.")

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to grab frame.")
            break

        cv2.putText(frame, "VISION TEST PASSED - PRESS 'Q' TO QUIT", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow("TripGuard - Camera Hardware Test", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    logger.info("Camera test completed and resources released.")

if __name__ == "__main__":
    test_camera()