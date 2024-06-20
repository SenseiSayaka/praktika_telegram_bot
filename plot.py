import matplotlib.pyplot as plt
#-*- coding: utf-8 -*-
def count_languages(filename, trigger_word, languages):
  """Считает количество упоминаний языков программирования."""
  language_counts = {}
  for lang in languages:
    language_counts[lang] = 0
  with open(filename, 'r') as file:
    for line in file:
      if trigger_word in line:
        for language in languages:
          if language in line:
            language_counts[language] += 1
  return language_counts

filename = 'bot.log'
trigger_word = "/prt"
languages = ["Rust", "Python", "C++", "C#"]

language_counts = count_languages(filename, trigger_word, languages)

# Сортировка языков по возрастанию количества упоминаний
sorted_languages = sorted(language_counts.items(), key=lambda item: item[1])

# Создание столбчатой диаграммы
plt.figure(figsize=(8, 5))
bars = plt.bar([lang for lang, count in sorted_languages],
               [i+1 for i in range(len(sorted_languages))])  # Место в топе

# Настройки диаграммы
plt.title("Топ языков программирования по упоминаниям")
plt.ylabel("Место в топе")

# Отображение количества упоминаний под столбцами
for bar, (lang, count) in zip(bars, sorted_languages):
    plt.text(bar.get_x() + bar.get_width() / 2,
             0.5,
             str(count),
             ha='center', va='bottom')

# Отображение названий языков на столбцах
for i, (lang, count) in enumerate(sorted_languages):
    plt.text(i, i + 1.1, lang, ha='center')

plt.show()