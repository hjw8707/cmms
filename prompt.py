from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

# 메뉴 항목을 정의합니다.
main_menu_items = ['옵션 1', '옵션 2', '옵션 3', '종료']
submenu_options = {
    '옵션 1': ['서브 옵션 1-1', '서브 옵션 1-2', '뒤로 가기'],
    '옵션 2': ['서브 옵션 2-1', '서브 옵션 2-2', '뒤로 가기'],
    '옵션 3': ['서브 옵션 3-1', '서브 옵션 3-2', '뒤로 가기'],
}

# WordCompleter를 사용하여 자동 완성을 설정합니다.
main_menu_completer = WordCompleter(main_menu_items + [str(i) for i in range(1, len(main_menu_items) + 1)], ignore_case=True)
session = PromptSession()

def display_menu(menu_items):
    print("\n=== 메뉴 ===")
    for idx, item in enumerate(menu_items, 1):
        print(f"{idx}. {item}")
    print("================")

def handle_option(menu_items, choice):
    if choice.isdigit():
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(menu_items):
            return menu_items[choice_idx]
    return choice

def main():
    while True:
        display_menu(main_menu_items)
        try:
            choice = session.prompt('메뉴를 선택하세요 (번호 또는 이름): ', completer=main_menu_completer)
            choice = handle_option(main_menu_items, choice)

            if choice == '종료':
                print('프로그램을 종료합니다.')
                break
            elif choice in submenu_options:
                while True:
                    display_menu(submenu_options[choice])
                    sub_choice = session.prompt(f'{choice}의 서브 메뉴를 선택하세요 (번호 또는 이름): ', completer=WordCompleter(submenu_options[choice], ignore_case=True))
                    sub_choice = handle_option(submenu_options[choice], sub_choice)

                    if sub_choice == '뒤로 가기':
                        break
                    elif sub_choice in submenu_options[choice]:
                        print(f'{choice}의 {sub_choice}를 선택하셨습니다.')
                    else:
                        print('잘못된 선택입니다. 다시 시도하세요.')
            else:
                print('잘못된 선택입니다. 다시 시도하세요.')

        except KeyboardInterrupt:
            print('\n프로그램을 종료합니다.')
            break
        except EOFError:
            print('\n프로그램을 종료합니다.')
            break

if __name__ == '__main__':
    main()
