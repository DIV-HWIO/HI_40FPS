import mil as MIL
import time
from collections import deque

class HookDataStruct():
    def __init__(self, MilDigitizer, MilImageDisp, ProcessedImageCount, LastTime):
        self.MilDigitizer = MilDigitizer
        self.MilImageDisp = MilImageDisp
        self.ProcessedImageCount = ProcessedImageCount
        self.LastTime = LastTime
        self.FrameTimes = deque(maxlen=30)  # 최근 30 프레임 시간 기록

BUFFERING_SIZE_MAX = 20
DISPLAY_INTERVAL = 4


def ProcessingFunction(HookType, HookId, HookDataPtr):
    ModifiedBufferId = MIL.MdigGetHookInfo(HookId, MIL.M_MODIFIED_BUFFER + MIL.M_BUFFER_ID)
    UserData = HookDataPtr

    CurrentTime = time.time()

    if UserData.LastTime != 0:
        delta = CurrentTime - UserData.LastTime
        if delta > 0:
            UserData.FrameTimes.append(delta)

    UserData.ProcessedImageCount += 1
    UserData.LastTime = CurrentTime

    # 이동 평균 FPS 계산
    if len(UserData.FrameTimes) > 5:
        avg_fps = 1 / (sum(UserData.FrameTimes) / len(UserData.FrameTimes))
        print(f"FPS (avg): {avg_fps:.2f}")

    # 화면 표시 (4프레임마다)
    if UserData.ProcessedImageCount % DISPLAY_INTERVAL == 0:
        MIL.MbufCopy(ModifiedBufferId, UserData.MilImageDisp)

    return 0


def MdigProcessExample():
   """ MIL을 이용한 실시간 영상 캡처 및 표시 예제 """

   MilApplication = MIL.MappAlloc("M_DEFAULT", MIL.M_DEFAULT)
   MilSystem = MIL.MsysAlloc(MIL.M_DEFAULT, MIL.M_SYSTEM_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT)

   MIL.MsysControl(MilSystem, MIL.M_NUMBER_OF_GRAB_BLOCKS, 1)

   MilDisplay = MIL.MdispAlloc(MilSystem, MIL.M_DEFAULT, "M_DEFAULT", MIL.M_DEFAULT)
   MilDigitizer = MIL.MdigAlloc(MilSystem, MIL.M_DEFAULT, "M_DEFAULT", MIL.M_DEFAULT)

   SizeX = MIL.MdigInquire(MilDigitizer, MIL.M_SIZE_X)
   SizeY = MIL.MdigInquire(MilDigitizer, MIL.M_SIZE_Y)

   MilImageDisp = MIL.MbufAllocColor(MilSystem, 3, SizeX, SizeY,
                                     8 + MIL.M_UNSIGNED,
                                     MIL.M_IMAGE + MIL.M_PROC + MIL.M_DISP + MIL.M_GRAB)

   MIL.MbufClear(MilImageDisp, MIL.M_COLOR_BLACK)
   MIL.MdispSelect(MilDisplay, MilImageDisp)
   MIL.MdispControl(MilDisplay, MIL.M_WINDOW_INITIAL_POSITION_X, 100)
   MIL.MdispControl(MilDisplay, MIL.M_WINDOW_INITIAL_POSITION_Y, 100)
   MIL.MdispControl(MilDisplay, MIL.M_TITLE, "MIL 실시간 표시 (4프레임마다 표시)")

   MilGrabBufferList = []
   MilGrabBufferListSize = 0
   for n in range(BUFFERING_SIZE_MAX):
      if n == 2:
         MIL.MappControl(MIL.M_DEFAULT, MIL.M_ERROR, MIL.M_PRINT_DISABLE)

      MilGrabBufferList.append(
         MIL.MbufAllocColor(MilSystem, 3, SizeX, SizeY, 8 + MIL.M_UNSIGNED,
                            MIL.M_IMAGE + MIL.M_GRAB + MIL.M_PROC + MIL.M_PACKED + MIL.M_BGR24)
      )

      if MilGrabBufferList[n] != MIL.M_NULL:
         MIL.MbufClear(MilGrabBufferList[n], 0xFF)
         MilGrabBufferListSize += 1
      else:
         break

   MIL.MappControl(MIL.M_DEFAULT, MIL.M_ERROR, MIL.M_PRINT_ENABLE)

   UserHookData = HookDataStruct(MilDigitizer, MilImageDisp, 0, 0)
   ProcessingFunctionPtr = MIL.MIL_DIG_HOOK_FUNCTION_PTR(ProcessingFunction)

   MIL.MdigProcess(MilDigitizer, MilGrabBufferList, MilGrabBufferListSize,
                   MIL.M_START, MIL.M_DEFAULT, ProcessingFunctionPtr, UserHookData)

   print("아무 키나 누르면 캡처를 중지합니다.\n")
   MIL.MosGetch()

   MIL.MdigProcess(MilDigitizer, MilGrabBufferList, MilGrabBufferListSize,
                   MIL.M_STOP, MIL.M_DEFAULT, ProcessingFunctionPtr, UserHookData)

   ProcessFrameCount = MIL.MdigInquire(MilDigitizer, MIL.M_PROCESS_FRAME_COUNT)
   ProcessFrameRate = MIL.MdigInquire(MilDigitizer, MIL.M_PROCESS_FRAME_RATE)

   if ProcessFrameRate > 0.0:
      print(f"\n\n총 {ProcessFrameCount:d} 프레임을 {ProcessFrameRate:.1f} FPS로 획득했습니다. "
            f"({1000.0/ProcessFrameRate:.1f} ms/프레임)")
   else:
      print("\n\n획득된 영상 데이터가 없습니다.\n")

   print("아무 키나 누르면 종료합니다.\n")
   MIL.MosGetch()

   for id in range(MilGrabBufferListSize):
      MIL.MbufFree(MilGrabBufferList[id])

   MIL.MbufFree(MilImageDisp)
   MIL.MdispFree(MilDisplay)
   MIL.MdigFree(MilDigitizer)
   MIL.MsysFree(MilSystem)
   MIL.MappFree(MilApplication)


if __name__ == "__main__":
   MdigProcessExample()
