# semantic-search-experiments
Масштабируемый поиск по эмбеддингам, основанный на Elastisearch 

## Инструкции по установке на Ubuntu:

### 1. Установка Docker
Шаг 1: Обновите систему
Откройте терминал и выполните команду:
```bash
sudo apt-get update

```
Шаг 2: Установите необходимые зависимости
Выполните команду:
```bash
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common

```
Шаг 3: Добавьте репозиторий Docker
Выполните команду:
```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

```
Шаг 4: Установите Docker
Выполните команду:
```bash
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

```
Шаг 5: Обновите систему и установите Docker
Выполните команду:
```bash
sudo apt-get update
sudo apt-get install docker-ce

```

### 2. Установка системы управления зависимостями и сборки проектов на языке Python
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Развёртывание проекта
Шаг 1: Клонируйте проект из git
```bash
git clone https://<git_repo>/semantic-search-experiments.git
```
Шаг 2: Сборка и запуск необходимых сервисов системы:
```bash
docker-compose up -d
```

Шаг 3: Создайте виртуальное окружение и запустите jupyter lab для создания поискового индекса
```bash
cd semantic-search-experiments 
poetry init
poetry shell
jupyter lab --ip 0.0.0.0 --no-browser --port=8888 --allow-root
```

Шаг 4: В браузере откройте запущенный jupyter и выполните ```prepare_labor_law_index.ipynb```

Шаг 5: Откройте в браузере ссылку основного приложения для поиска на основе настроек ```docker-compose.yaml```


