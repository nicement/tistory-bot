import pickle, time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def save_cookies():
    options = Options()
    # options.add_argument('--headless')  # headless 모드 해제: 사람이 직접 로그인해야 하므로
    driver = webdriver.Chrome(options=options)

    # 티스토리 로그인 페이지
    driver.get("https://www.tistory.com/auth/login")

    print("로그인 및 2차 인증을 완료한 후 Enter 키를 누르세요...")
    input()

    # 쿠키 저장
    cookies = driver.get_cookies()
    with open("tistory_cookies.pkl", "wb") as f:
        pickle.dump(cookies, f)

    print("✅ 쿠키 저장 완료")
    driver.quit()

def load_cookies_and_post(title, content):
    options = Options()
    # options.add_argument('--headless')  # 자동 실행 시 headless 모드 추천
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)

    # 티스토리 홈으로 이동 후 쿠키 주입
    driver.get("https://www.tistory.com/")
    with open("tistory_cookies.pkl", "rb") as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            # domain 키가 없으면 생략
            cookie.pop('sameSite', None)
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print("쿠키 추가 실패:", e)

    # 로그인된 상태로 블로그 글쓰기 페이지 이동
    
    driver.get("https://iam-ai.tistory.com/manage/newpost")
    time.sleep(3)

    # 작성 중인 글 사용 여부 alert가 뜨면 '아니오' 클릭
    try:
        alert = driver.switch_to.alert
        print(f"Alert 발생: {alert.text}")
        # '아니오' 버튼은 일반적으로 dismiss()로 처리
        alert.dismiss()
        print("'아니오' 선택 완료")
        time.sleep(1)
    except Exception as e:
        print("작성 중인 글 alert 없음 또는 처리 실패:", e)

    # 작성 모드 변경 시 alert가 뜨면 자동으로 확인 클릭 (반복적으로 발생할 수 있으므로 루프 처리)
    try:
        mode_btn = driver.find_element(By.ID, "editor-mode-layer-btn-open")
        mode_btn.click()
        markdown_btn = driver.find_element(By.ID, "editor-mode-markdown")
        markdown_btn.click()
        time.sleep(3)
        # alert가 떠 있으면 반복적으로 모두 닫기
        while True:
            try:
                alert = driver.switch_to.alert
                print(f"Alert 발생: {alert.text}")
                alert.accept()
                time.sleep(1)
            except:
                break
    except Exception as e:
        # 혹시 남아있는 alert가 있으면 닫기
        try:
            while True:
                alert = driver.switch_to.alert
                print(f"Alert 발생: {alert.text}")
                alert.accept()
                time.sleep(1)
        except:
            pass
        print("작성 모드 버튼 처리 중 예외 발생:", e)

    time.sleep(3)

    # 제목 입력
    title_input = driver.find_element(By.ID, "post-title-inp")
    title_input.send_keys(title)

    # CodeMirror 마크다운 에디터에 본문 입력 (iframe이 아닌 div 내부)
    try:
        cm_div = driver.find_element(By.CSS_SELECTOR, ".CodeMirror.cm-s-tistory-markdown")
        driver.execute_script("arguments[0].CodeMirror.setValue(arguments[1]);", cm_div, content)
        print("CodeMirror 마크다운 에디터에 본문 입력 완료(JS)")
    except Exception as e:
        print("CodeMirror 마크다운 에디터 입력 실패:", e)
        driver.quit()
        return

    time.sleep(1)

    # 발행 버튼 찾기: id='publish-layer-btn'로 직접 찾기
    try:
        publish_btn = driver.find_element(By.ID, "publish-layer-btn")
    except Exception:
        # 모든 button 태그의 텍스트와 class 출력 (디버깅용)
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"페이지 내 button 개수: {len(buttons)}")
        for idx, btn in enumerate(buttons):
            print(f"button {idx}: text='{btn.text}', class='{btn.get_attribute('class')}', id='{btn.get_attribute('id')}'")
        print("발행(완료) 버튼을 찾지 못했습니다.")
        driver.quit()
        return
    publish_btn.click()
    time.sleep(1)

    # 완료 버튼 클릭 후 나오는 div에서 '비공개 저장' 버튼 클릭
    try:
        private_save_btn = driver.find_element(By.ID, "publish-btn")
        private_save_btn.click()
        print("✅ 비공개 저장 버튼 클릭 완료")
    except Exception as e:
        print("비공개 저장 버튼을 찾지 못했습니다:", e)
        driver.quit()
        return

    print("✅ 글 작성 및 비공개 저장 완료")
    time.sleep(3)
    driver.quit()

if __name__ == "__main__":
    # title, content를 파일에서 읽어옴 (예: post.txt)
    post_file = "post.txt"
    if os.path.exists(post_file):
        with open(post_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            title = lines[0].strip() if len(lines) > 0 else "테스트 제목"
            content = "".join(lines[1:]).strip() if len(lines) > 1 else "작성된 글 내용입니다."
    else:
        title = "테스트 제목"
        content = "작성된 글 내용입니다."
    # 쿠키 파일이 있으면 save_cookies 생략
    if not os.path.exists("tistory_cookies.pkl"):
        save_cookies()
    load_cookies_and_post(title, content)