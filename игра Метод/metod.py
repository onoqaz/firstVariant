#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МЕТОД — текстовый прототип симулятора диагностики автоэлектрики.
Ядро: декларативная модель дела (цепь + неисправность + эталонные измерения).
Игрок выбирает действия, тратит время/заряд АКБ и получает очки за МЕТОД,
а не за угаданный ответ.

Запуск:  python3 metod.py
Документация идеи: папка «игра Метод».
"""

import json
import textwrap


# ----------------------------------------------------------------------------
# МОДЕЛЬ ДАННЫХ ДЕЛА
# ----------------------------------------------------------------------------
# Каждое дело описывается декларативно. Измерения — это «данные, а не логика»:
# движок лишь отдаёт заранее заданные значения по запросу инструмента.
#
# Ключи measurements: (зона/узел, количество) -> строка ответа.
#   количества: "U" напряжение, "R" сопротивление, "cont" прозвонка,
#               "drop" падение напряжения на массе.
# checklist — шаги алгоритма из модуля 20 (для дебрифа).
# repairs — доступные ремонтные действия: name, cost_min, money, correct(bool),
#           desc.
# ----------------------------------------------------------------------------

CASES = {
    "c1_window": {
        "id": "c1_window",
        "tier": 1,
        "algorithm": "known_fault",
        "title": "Не работает стеклоподъёмник водителя",
        "car": "Седан 2015",
        "client": "бабушка",
        "complaint": "Стекло водителя не поднимается и не опускается с кнопки.",
        "budget_min": 120,
        "battery_soc": 85,
        "zones": {
            "A": "Дверь водителя (камера)",
            "B": "Блок предохранителей",
            "C": "Приборная панель/кнопка",
        },
        "interview": {
            "symptom": "Не работает ТОЛЬКО водительское стекло, остальные работают.",
            "condition": "После мойки машины в салоне.",
            "history": "Сам ничего не крутил, к мастерам не обращался.",
            "self_fix": "Нет, кустарного ремонта не было.",
            "bad_q": "Вы точно льёте хороший бензин? — Клиентка обижается и замолкает.",
        },
        "inspect": {
            "A": "Видна подозрительная протёртость изоляции провода в гофре двери.",
            "B": "Предохранитель F27 цел, реле K1 щёлкает при нажатии кнопки.",
            "C": "Кнопка ходит нормально, нажимается до упора.",
        },
        "measurements": {
            ("B", "cont"): "F27 цел (звонится). K1 приходит управление от кнопки.",
            ("A", "U"): "На пине 2 разъёма X106 при нажатии кнопки 12.4 В — есть.",
            ("A", "drop"): "Падение напряжения от пина 1 до кузова 0.05 В — норма.",
            ("A", "R_motor"): "Подача 12 В напрямую на мотор — НЕ крутится.",
            ("A", "cont2"): "Прозвонка обмотки мотора — обрыв (бесконечность).",
        },
        "dtc": [],
        "correct_cause": "F12_обрыв_обмотки_мотора",
        "hidden_truth": "Обмотка мотора стеклоподъёмника сгорела (обрыв).",
        "checklist": [
            "опрос владельца", "визуальный осмотр", "проверка предохранителя/реле",
            "проверка питания", "проверка массы", "проверка управления",
            "проверка компонента", "ремонт", "верификация",
        ],
        "repairs": [
            {"name": "Заменить мотор стеклоподъёмника M",
             "cost_min": 60, "money": 3200, "correct": True,
             "desc": "Установить исправный мотор, адаптация кнопки."},
            {"name": "Заменить блок предохранителей",
             "cost_min": 60, "money": 5400, "correct": False,
             "desc": "Дорогая и бесполезная замена — причина не в нём."},
            {"name": "Прошить блок комфорта",
             "cost_min": 45, "money": 2500, "correct": False,
             "desc": "Софт ни при чём; симптом вернётся."},
        ],
    },

    "c2_flicker": {
        "id": "c2_flicker",
        "tier": 2,
        "algorithm": "known_fault",
        "title": "Мерцают фары ближнего света",
        "car": "Хэтчбек 2014",
        "client": "таксист",
        "complaint": "Ближний свет мерцает, сильнее при повороте руля. На холостых.",
        "budget_min": 150,
        "battery_soc": 80,
        "zones": {
            "A": "Под капотом (фара, масса)",
            "B": "Блок предохранителей",
            "C": "Подрулевой переключатель",
        },
        "interview": {
            "symptom": "Мерцает ближний свет, не гаснет полностью, а пульсирует.",
            "condition": "На холостых, усиливается при повороте руля.",
            "history": "После мойки высоким давлением под капотом.",
            "self_fix": "Нет.",
            "bad_q": "Может, лампочку не того цвета поставили? — Клиент вздыхает.",
        },
        "inspect": {
            "A": "Провод массы фары перетёрт о кромку, видно оголённый провод.",
            "B": "Предохранитель F12 цел.",
            "C": "Переключатель света щёлкает чётко.",
        },
        "measurements": {
            ("A", "U"): "На фаре H7 13.8 В под нагрузкой — в норме.",
            ("A", "drop"): "Падение напряжения фара→кузов 0.8 В (норма <0.1 В)!",
            ("C", "cont"): "Управление от переключателя до реле — исправно.",
            ("A", "R_bulb"): "Сама лампа целая, прозванивается.",
        },
        "dtc": [],
        "correct_cause": "F04_окисление_массы_фары",
        "hidden_truth": "Окисление и перетирание провода массы фары (плохой контакт).",
        "checklist": [
            "опрос владельца", "визуальный осмотр", "проверка предохранителя/реле",
            "проверка питания", "проверка массы", "проверка управления",
            "проверка компонента", "ремонт", "верификация",
        ],
        "repairs": [
            {"name": "Зачистить и восстановить провод массы фары",
             "cost_min": 40, "money": 600, "correct": True,
             "desc": "Зачистка, пайка, термоусадка, заземление на чистый болт."},
            {"name": "Заменить блок фары H7 в сборе",
             "cost_min": 50, "money": 4200, "correct": False,
             "desc": "Лампа и разъём исправны — деньги на ветер."},
            {"name": "Менять генератор",
             "cost_min": 90, "money": 9000, "correct": False,
             "desc": "Напряжение заряда в норме, причина не здесь."},
        ],
    },

    "c3_draw": {
        "id": "c3_draw",
        "tier": 3,
        "algorithm": "unknown_fault",
        "title": "«Машина сама сажает аккумулятор по ночам»",
        "car": "Универсал 2013",
        "client": "курьер",
        "complaint": "По утрам вяло крутит стартер, иногда ночью что-то жужжит в салоне.",
        "budget_min": 180,
        "battery_soc": 60,
        "zones": {
            "A": "Моторный отсек / АКБ",
            "B": "Блок предохранителей",
            "C": "Салон / печка",
            "D": "Дополнительное оборудование (регистратор)",
        },
        "interview": {
            "symptom": "Утром вялый пуск; ночью слышен жужжащий звук из салона.",
            "condition": "Проявляется после ночёвки; летом чаще.",
            "history": "Две недели назад установили видеорегистратор с автовыключением.",
            "self_fix": "Менял АКБ на новый — не помогло.",
            "bad_q": "Может, масло старое? — Клиент качает головой.",
        },
        "inspect": {
            "A": "АКБ 12.4 В покоя, клеммы чистые.",
            "B": "Все предохранители целы визуально.",
            "C": "Реле вентилятора печки греется.",
            "D": "Регистратор подключён к постоянному плюсу, не отключается.",
        },
        "measurements": {
            ("A", "U"): "Напряжение покоя АКБ 12.4 В.",
            ("A", "leak"): "Утечка тока 3.8 А (!) в спящем режиме (норма <0.03 А).",
            ("B", "isol_K7"): "После вынимания реле K7 (вентилятор) утечка исчезла.",
            ("D", "U"): "На регистраторе постоянно 12.4 В, управления нет.",
        },
        "dtc": ["B1234 (актуальный)", "U0130 (в истории)"],
        "correct_cause": "F10_залипшее_реле_или_F13_утечка",
        "hidden_truth": "Реле вентилятора печки залипло + регистратор на постоянном плюсе.",
        "checklist": [
            "опрос владельца", "визуальный осмотр", "базовая проверка АКБ",
            "замер утечки тока", "считывание кодов", "анализ общих точек",
            "метод изоляции", "ремонт", "верификация",
        ],
        "repairs": [
            {"name": "Заменить залипшее реле K7 и переключить регистратор на ACC",
             "cost_min": 50, "money": 900, "correct": True,
             "desc": "Убрать постоянную нагрузку и залипание вентилятора."},
            {"name": "Купить новый аккумулятор",
             "cost_min": 30, "money": 8000, "correct": False,
             "desc": "Утечка останется — утром опять вялый пуск."},
            {"name": "Менять блок комфорта",
             "cost_min": 60, "money": 6000, "correct": False,
             "desc": "Причина в реле и проводке, не в блоке."},
        ],
    },
}


# ----------------------------------------------------------------------------
# СОСТОЯНИЕ ИГРЫ
# ----------------------------------------------------------------------------

class Game:
    def __init__(self, case):
        self.case = case
        self.time_left = case["budget_min"]
        self.battery = case["battery_soc"]
        self.reputation = 50
        self.money = 0
        self.used_actions = set()
        self.notes = []
        self.interview_done = 0
        self.hypothesis = None
        self.repaired = False
        self.verified = False
        self.log = []

    def spend(self, minutes):
        self.time_left -= minutes
        if self.time_left < 0:
            self.time_left = 0

    def drain_battery(self, amount):
        self.battery = max(0, self.battery - amount)

    def note(self, text):
        self.log.append(text)

    def status(self):
        return (f"Время: {self.time_left}/{self.case['budget_min']} мин | "
                f"АКБ: {self.battery}% | Репутация: {self.reputation} | "
                f"Деньги: {self.money} ₽")

    def add_money(self, amount):
        self.money += amount


# ----------------------------------------------------------------------------
# ДЕЙСТВИЯ
# ----------------------------------------------------------------------------

def act_interview(g):
    print("\n-- ОПРОС ВЛАДЕЛЬЦА --")
    q = g.case["interview"]
    questions = [
        ("1", "symptom", "Что именно происходит?"),
        ("2", "condition", "При каких условиях проявляется?"),
        ("3", "history", "Были ли работы, мойка, установка оборудования?"),
        ("4", "self_fix", "Были ли попытки самолечения?"),
    ]
    print("Доступные вопросы:")
    for key, _, text in questions:
        print(f"  [{key}] {text}")
    print("  [5] Плохой вопрос (потерять терпение клиента)")
    choice = input("Выберите вопрос (или Enter — завершить): ").strip()
    if choice == "":
        return
    if choice == "5":
        g.spend(5)
        g.reputation = max(0, g.reputation - 2)
        print("?", q.get("bad_q", "Клиент недоволен."))
        g.note("Опрос: задан неуместный вопрос (−репутация).")
        return
    for key, field, _ in questions:
        if choice == key:
            g.spend(5)
            g.used_actions.add("опрос владельца")
            print("Клиент:", q[field])
            g.note(f"Опрос: {field} — {q[field]}")
            return
    print("Нет такого вопроса.")


def act_inspect(g):
    print("\n-- ВИЗУАЛЬНЫЙ ОСМОТР --")
    for zid, zname in g.case["zones"].items():
        print(f"  [{zid}] {zname}")
    z = input("Выберите зону: ").strip().upper()
    if z in g.case["inspect"]:
        g.spend(10)
        g.used_actions.add("визуальный осмотр")
        print(f"[{z}] {g.case['inspect'][z]}")
        g.note(f"Осмотр {z}: {g.case['inspect'][z]}")
    else:
        print("Такой зоны нет.")


def act_multimeter(g):
    print("\n-- МУЛЬТИМЕТР --")
    print("Режимы: 1 напряжение(U)  2 сопротивление/прозвонка(R/cont)  "
          "3 падение на массе(drop)  4 утечка тока(leak)")
    mode = input("Режим: ").strip()
    node = input("Узел/зона (напр. A, B, K7, D): ").strip().upper()
    # подключение к новой зоне стоит +10, само измерение +15
    g.spend(10 + 15)
    key = None
    if mode in ("1", "U"):
        key = (node, "U")
    elif mode in ("2", "R", "cont"):
        key = (node, "R_motor") if "motor" in node else (node, "cont")
        if mode in ("2", "R", "cont") and (node, "cont2") not in g.case["measurements"]:
            key = (node, "cont")
    elif mode == "drop":
        key = (node, "drop")
    elif mode == "leak":
        key = (node, "leak")
    else:
        print("Неизвестный режим.")
        return
    if key in g.case["measurements"]:
        # обесточенная цепь требуется для сопротивления
        if mode in ("2", "R", "cont"):
            print("ПРЕДУПРЕЖДЕНИЕ: сопротивление меряют на обесточенной цепи.")
        g.used_actions.add("проверка компонента" if "R" in mode or "cont" in mode
                           else "проверка питания" if mode in ("1", "U")
                           else "проверка массы" if mode == "drop" else "замер утечки")
        print("Показание:", g.case["measurements"][key])
        g.note(f"Мультиметр {node}/{mode}: {g.case['measurements'][key]}")
    else:
        print("Нет данных для этого узла в выбранном режиме.")
    g.drain_battery(1)


def act_scanner(g):
    print("\n-- СКАНЕР OBD-II --")
    print(" 1 Считать коды  2 Live data  3 Стереть коды")
    c = input("Выбор: ").strip()
    if c == "1":
        g.spend(20)
        g.used_actions.add("считывание кодов")
        if g.case["dtc"]:
            print("Коды:", ", ".join(g.case["dtc"]))
            g.note("Коды: " + ", ".join(g.case["dtc"]))
        else:
            print("Активных кодов нет.")
    elif c == "2":
        g.spend(15)
        print("Live data недоступно в этой демо-версии (нужен проф. сканер).")
    elif c == "3":
        g.spend(10)
        print("Коды стёрты (часть верификации).")
        g.used_actions.add("верификация")
    else:
        print("Нет такого пункта.")


def act_isolation(g):
    print("\n-- ИЗОЛЯЦИЯ (метод выключения) --")
    item = input("Что вынуть/отключить (напр. K7, F12): ").strip().upper()
    g.spend(10)
    g.used_actions.add("метод изоляции")
    key = (item, "isol_" + item)
    if key in g.case["measurements"]:
        print(g.case["measurements"][key])
        g.note(f"Изоляция {item}: {g.case['measurements'][key]}")
    else:
        print(f"После отключения {item} изменений не видно (или не применимо).")


def act_hypothesis(g):
    print("\n-- ГИПОТЕЗА --")
    print("Текущая:", g.hypothesis or "—")
    h = input("Сформулируйте предполагаемую причину: ").strip()
    if h:
        g.hypothesis = h
        print("Гипотеза записана. Подкрепите её измерениями в журнале.")


def act_repair(g):
    print("\n-- РЕМОНТ --")
    if g.repaired:
        print("Ремонт уже выполнен. Перейдите к верификации.")
        return
    for i, r in enumerate(g.case["repairs"], 1):
        mark = "★" if r["correct"] else " "
        print(f"  [{i}] {mark} {r['name']}  ({r['cost_min']} мин, {r['money']} ₽)")
    print("  [0] Отмена")
    c = input("Выберите действие: ").strip()
    if c == "0" or c == "":
        return
    try:
        idx = int(c) - 1
        r = g.case["repairs"][idx]
    except (ValueError, IndexError):
        print("Неверный выбор.")
        return
    g.spend(r["cost_min"])
    g.add_money(-r["money"])
    g.used_actions.add("ремонт")
    print("Выполнено:", r["desc"])
    g.note(f"Ремонт: {r['name']}")
    if r["correct"]:
        g.repaired = True
        g.hidden_fixed = True
        print("✓ Неисправность устранена.")
    else:
        g.reputation = max(0, g.reputation - 5)
        print("✗ Симптом остался. Клиент недоволен (−репутация). "
              "Деньги за деталь потрачены.")


def act_verify(g):
    print("\n-- ВЕРИФИКАЦИЯ --")
    if not g.repaired:
        print("Нельзя подтвердить ремонт до его выполнения.")
        g.spend(5)
        return
    g.spend(20)
    g.used_actions.add("верификация")
    print("Симптом устранён, коды чисты, контрольный запуск пройден.")
    g.verified = True
    g.add_money(2400)
    g.reputation = min(100, g.reputation + 2)
    print("✓ Дело закрыто. Оплата начислена.")


def act_log(g):
    print("\n-- ЖУРНАЛ ИЗМЕРЕНИЙ --")
    if not g.log:
        print("(пусто)")
    for line in g.log:
        print(" •", line)


def act_quit(g):
    print("\nДело брошено. Клиент ушёл.")
    g.reputation = max(0, g.reputation - 10)


# ----------------------------------------------------------------------------
# ДЕБРИФ И ОЧКИ
# ----------------------------------------------------------------------------

def debrief(g):
    print("\n" + "=" * 60)
    print("ДЕБРИФ ПО ЧЕКЛИСТУ АЛГОРИТМА")
    print("=" * 60)
    check = g.case["checklist"]
    done = g.used_actions
    print(f"{'Шаг':<32}{'Статус'}")
    for step in check:
        ok = step in done
        print(f"  {step:<30}{'✓' if ok else '— пропущено'}")
    covered = sum(1 for s in check if s in done)
    k_method = round(0.5 + 0.8 * (covered / len(check)), 2)
    budget = g.case["budget_min"]
    fact = budget - g.time_left
    k_time = min(1.2, round(budget / max(1, fact), 2))
    penalty = 0
    reasons = []
    # штраф за слепую/неверную замену: запись ремонта без корректного действия
    wrong = 0
    for n in g.log:
        if n.startswith("Ремонт:"):
            txt = n[len("Ремонт:"):]
            if not any(r["name"] in txt and r["correct"] for r in g.case["repairs"]):
                wrong += 1
    if wrong:
        penalty += 300 * wrong
        reasons.append(f"слепая/неверная замена ×{wrong} (−{300*wrong})")
    if not g.verified and g.repaired:
        penalty += 200
        reasons.append("нет верификации (−200)")
    if g.battery <= 0:
        penalty += 100
        reasons.append("АКБ разряжен в работе (−100)")
    score = max(0, int(1000 * k_method * k_time - penalty))
    print("\nИстина дела:", g.case["hidden_truth"])
    print(f"Покрытие чеклиста: {covered}/{len(check)}  → K_метод={k_method}")
    print(f"Время: {fact}/{budget} мин  → K_время={k_time}")
    if reasons:
        print("Штрафы:", "; ".join(reasons))
    print(f"\nИТОГОВЫЕ ОЧКИ: {score}")
    print(f"Репутация: {g.reputation} | Деньги: {g.money} ₽")
    print("=" * 60)


# ----------------------------------------------------------------------------
# ГЛАВНЫЙ ЦИКЛ ОДНОГО ДЕЛА
# ----------------------------------------------------------------------------

def play_case(case_id):
    case = CASES[case_id]
    g = Game(case)
    print("\n" + "#" * 60)
    print(f"ДЕЛО: {case['title']}")
    print(f"Авто: {case['car']} | Клиент: {case['client']}")
    print(f"Жалоба: {case['complaint']}")
    print("#" * 60)
    while True:
        print("\n" + g.status())
        print("МЕНЮ: [1]Опрос [2]Осмотр [3]Мультиметр [4]Сканер "
              "[5]Изоляция [6]Гипотеза [7]Ремонт [8]Верификация "
              "[9]Журнал [0]Уйти")
        cmd = input(">> ").strip()
        if cmd == "1":
            act_interview(g)
        elif cmd == "2":
            act_inspect(g)
        elif cmd == "3":
            act_multimeter(g)
        elif cmd == "4":
            act_scanner(g)
        elif cmd == "5":
            act_isolation(g)
        elif cmd == "6":
            act_hypothesis(g)
        elif cmd == "7":
            act_repair(g)
        elif cmd == "8":
            act_verify(g)
            if g.verified:
                break
        elif cmd == "9":
            act_log(g)
        elif cmd == "0":
            act_quit(g)
            break
        else:
            print("Неизвестная команда.")
        # защита: время вышло и ремонт не выполнен — дело провалено
        if g.time_left <= 0 and not g.repaired:
            print("\nВремя вышло, дело не закрыто.")
            g.reputation = max(0, g.reputation - 10)
            break
    debrief(g)
    return g


def main():
    print("МЕТОД — текстовый тренажёр диагноста автоэлектрика (демо).")
    print("Доступные дела:")
    for cid, c in CASES.items():
        print(f"  [{cid}] (ступень {c['tier']}) {c['title']}")
    cid = input("Введите id дела: ").strip()
    if cid not in CASES:
        print("Нет такого дела. Запускаю c1_window по умолчанию.")
        cid = "c1_window"
    play_case(cid)


if __name__ == "__main__":
    main()
