function changeImage() {
    let toggleBtn = document.getElementById('imgClickAndChange');
    let dropDownMenu = document.querySelector('.dropdown_menu');

    dropDownMenu.classList.toggle('open');
    let isOpen = dropDownMenu.classList.contains('open');

    toggleBtn.src = isOpen ? 'images/xmark-solid.svg' : 'images/bars-solid.svg';
}
window.onload = function() {
    let toggleBtn = document.getElementById('imgClickAndChange');
    let toggleBtnIcon = document.querySelector('.toggle_btn i');
    let dropDownMenu = document.querySelector('.dropdown_menu');

    toggleBtn.onclick = function() {
        changeImage();
    }
}

var host = window.location.origin;
function createDashboard(){
    fetch(host + '/IOT_Devices/get-range-source')
    .then(response => response.json())
    .then(json => {
        
        console.log(json.source_id);

        var filteredJSON = json.source_id.reduce(function(result, current, index) {
            if (json.min_range[index] && json.max_range[index] != '') {
                result.push({ 
                    "id": json.id[index], 
                    "source_id": current, 
                    "location_description": json.location_description[index],
                    "location_cor_1": json.location_cor_1[index],
                    "location_cor_2": json.location_cor_2[index],
                    "property_name": json.property_name[index],
                    "min_range": json.min_range[index],
                    "max_range": json.max_range[index],
                    "properties_id": json.properties_id[index],
                    "property_name_rus": json.property_name_rus[index],
                    "type_id": json.type_id[index],
                    "value": json.value[index],
                    "datetime": json.datetime[index]
                });
            }
            return result;
        }, []); 

        console.log(filteredJSON);

        function updateDashboard(data) {
            const dashboard = document.querySelector('.dashboard');
            dashboard.innerHTML = '';

            const uniqueLevels = {};
            const statusCounts = {};

            data.forEach(location => {
                const locationSplit = location.location_description.split(' - ');
                const level_1 = locationSplit[0];
                const level_2 = locationSplit[1];
                const level_3 = location.source_id;
                const properties_id = location.properties_id;
                const location_cor_1 = location.location_cor_1;
                const location_cor_2 = location.location_cor_2;

                // Проверяем, было ли уже такое значение level_2
                if (!uniqueLevels[level_2]) {
                    uniqueLevels[level_2] = {
                        ok: 0,
                        intermediate: 0,
                        noConnection: 0,
                        level_1: level_1,
                        level_3: []
                    };
                }
                console.log(uniqueLevels[level_2]);
                // Функция форматирующая datetime
                function parseDateTime(dateTimeString) {
                    // Извлечение числового значения из строки
                    const numericValue = parseInt(dateTimeString.replace('/Date(', '').replace(')/', ''), 10);

                    // Создание объекта Date на основе числового значения
                    return new Date(numericValue);
                }

                let propertyValue = parseFloat(location.value);
                let minRange = parseFloat(location.min_range);
                let maxRange = parseFloat(location.max_range);
                let currentTime = new Date;
                let locationDateTime
                if (location.datetime === null) {
                    locationDateTime = 0;
                } else {
                    locationDateTime = parseDateTime(location.datetime);
                }
            
                // Расчет разницы во времени в минутах
                const timeDiffInMinutes = Math.abs((currentTime - locationDateTime) / (1000 * 60));
                // Отладка значений времени
                console.log(`datetime: ${locationDateTime}, currentTime: ${currentTime}, diff: ${timeDiffInMinutes}`);

                // Обновляем счетчики статусов для этой локации
                if ((minRange && maxRange) !== '') {
                    if (timeDiffInMinutes > 30) {
                        uniqueLevels[level_2].noConnection++;
                    } else if (propertyValue < minRange || propertyValue > maxRange) {
                        uniqueLevels[level_2].intermediate++;
                    } else if (propertyValue > minRange && propertyValue < maxRange) {
                        uniqueLevels[level_2].ok++;
                    }
                }

                // Добавляем уникальное значение level_3 в массив
                if (!uniqueLevels[level_2].level_3.includes(level_3)) {
                    uniqueLevels[level_2].level_3.push(level_3);
                }

                // Обновляем statusCounts для отображения состояний датчиков на странице "Детальный вид"
                if (!statusCounts[level_3]) {
                    statusCounts[level_3] = {
                        level_1: level_1,
                        level_2: level_2,
                        level_3: level_3,
                        ok: 0,
                        intermediate: 0,
                        noConnection: 0,
                        location_cor_1: location_cor_1,
                        location_cor_2: location_cor_2
                    };
                }
                if ((minRange && maxRange) !== '') {
                    if (timeDiffInMinutes > 30) {
                        statusCounts[level_3].noConnection++;
                    } else if (propertyValue < minRange || propertyValue > maxRange) {
                        statusCounts[level_3].intermediate++;
                    } else if (propertyValue > minRange && propertyValue < maxRange) {
                        statusCounts[level_3].ok++;
                    }
                }
            });

            console.log(statusCounts);

            // Функция для Яндекс Карт
            function getStatusColor(ok, intermediate, noConnection) {
                if (noConnection > 0) {
                    return 'ff0000'; // Красный
                } else if (intermediate > 0) {
                    return 'ffa500'; // Оранжевый
                } else if (ok > 0) {
                    return '00ff00'; // Зеленый
                } else {
                    return '808080'; // Серый
                }
            }

            // Создание Яндекс Карт
            document.addEventListener('DOMContentLoaded', function() {
                function initMap() {
                    var map = new ymaps.Map("map", {
                        center: [58.01, 56.25],
                        zoom: 10
                    });

                    // Перебираем объекты в statusCounts и создаем на карте метки
                    for (var level3 in statusCounts) {
                        if (statusCounts.hasOwnProperty(level3)) {
                            var item = statusCounts[level3];
                            var coords = [item.location_cor_1, item.location_cor_2];
                            var statusName = '';

                            if (item.noConnection > 0) {
                                statusName = 'Нет связи';
                            } else if (item.intermediate > 0) {
                                statusName = 'Отклонение';
                            } else {
                                statusName = 'Норма';
                            }

                            // Создаем метку
                            var placemark = new ymaps.Placemark(coords, {
                                balloonContent: `
                                    <b>Объект:</b> ${item.level_1}<br>
                                    <b>Локация:</b> ${item.level_2}<br>
                                    <b>Состояние:</b>
                                    <ul>
                                        <li>${statusName}</li>
                                    </ul>
                                `
                            }, {
                                preset: 'islands#circleIcon',
                                iconColor: '#' + getStatusColor(item.ok, item.intermediate, item.noConnection)
                            });

                            map.geoObjects.add(placemark);
                        }
                    }
                }

                ymaps.ready(initMap);
            });

            // После обработки всех локаций, создаем карточки
            for (const level_2 in uniqueLevels) {
                const { ok, intermediate, noConnection, level_1, level_3 } = uniqueLevels[level_2];
                const card = document.createElement('div');
                card.className = 'card';

                // card.setAttribute('onclick', "location.href='heater_controller.html';");

                const status = document.createElement('div');
                status.className = 'status';

                const textDiv = document.createElement('div');
                textDiv.className = 'text-div';

                const statusList = document.createElement('ul');
                statusList.className = 'status-list';
                const statusItem = document.createElement('li');

                card.appendChild(status);
                card.appendChild(textDiv);

                statusList.appendChild(statusItem);
                textDiv.appendChild(statusList);

                const title1 = document.createElement('h3');
                const title2 = document.createElement('h3');
                const title3 = document.createElement('h3');
                title1.textContent = level_1;
                title1.classList.add('level-1');
                title2.textContent = level_2;
                title2.classList.add('level-2');
                title3.textContent = uniqueLevels[level_2].level_3;
                title3.classList.add('level-3');
                title3.style.display = "none";
                textDiv.appendChild(title1);
                textDiv.appendChild(title2);
                textDiv.appendChild(title3);

                console.log(`ok: ${uniqueLevels[level_2].ok}, intermediate: ${uniqueLevels[level_2].intermediate}, noConnection: ${uniqueLevels[level_2].noConnection}, level_3: ${uniqueLevels[level_2].level_3}`);

                // Добавление класса статуса на основе подсчета
                if (noConnection > 0) {
                    status.classList.add('status-no-connection');
                    statusList.style.color = '#F44336';
                    title1.style.color = '#000';
                    title2.style.color = '#898686';
                    title2.style.fontSize = '0.9em';
                    title2.style.fontWeight = '400';
                    statusItem.textContent = 'Нет связи!';
                } else if (intermediate > 0) {
                    status.classList.add('status-intermediate');
                    statusList.style.color = '#FFC107';
                    title1.style.color = '#000';
                    title2.style.color = '#898686';
                    title2.style.fontSize = '0.9em';
                    title2.style.fontWeight = '400';
                    statusItem.textContent = 'Отклонение!';
                } else if (ok > 0) {
                    status.classList.add('status-ok');
                    statusList.style.color = '#4CAF50';
                    title1.style.color = '#000';
                    title2.style.color = '#898686';
                    title2.style.fontSize = '0.9em';
                    title2.style.fontWeight = '400';
                    statusItem.textContent = 'Все ок';
                }

                dashboard.appendChild(card);
            }
            const locationCards = document.querySelectorAll('.card');

            // Сохраняем нажатые локации и переходим на вторую страницу
            locationCards.forEach(card => {
                card.addEventListener('click', (event) => {
                    const locationElement_1 = card.querySelector('.level-1');
                    const locationElement_2 = card.querySelector('.level-2');
                    const locationElement_3 = card.querySelector('.level-3');
                    const undefinedState = 'undefined';

                    let newStatusCounts = {};

                    // Чистим все переменные в localStorage
                    localStorage.clear();

                    if (locationElement_1) {
                        const locationName = locationElement_1.textContent;
                        localStorage.setItem(`level-${locationName.replace(/\s/g, '_')}-${undefinedState}-open`, true);
                        console.log(localStorage.getItem(`level-${locationName.replace(/\s/g, '_')}-undefined-open`));
                    }
                    if (locationElement_2) {
                        const locationName = locationElement_2.textContent;
                        localStorage.setItem(`level-${undefinedState}-${locationName.replace(/\s/g, '_')}-open`, true);
                        console.log(localStorage.getItem(`level-undefined-${locationName.replace(/\s/g, '_')}-open`));
                    }
                    // Записываем в localStorage все уникальные level_3
                    if (locationElement_3) {
                        const locationName = locationElement_3.textContent;
                        let level3Split = locationName.split(",");
                        localStorage.setItem('selectedLevel3', level3Split);
                        console.log(localStorage.getItem('selectedLevel3'));

                        level3Split.forEach(item => {
                          if (statusCounts.hasOwnProperty(item)) {
                            newStatusCounts[item] = statusCounts[item];
                          }
                        });
                    }
                    console.log(statusCounts);

                    console.log(newStatusCounts);

                    localStorage.setItem('newStatusCounts', JSON.stringify(newStatusCounts));

                    // Переходим на вторую страницу
                    window.location.href = 'heater_controller.html';
                });
            });
        }
        updateDashboard(filteredJSON);
    })
}
window.onload = createDashboard();

// ---------------------------------- НЕ ЗАБЫТЬ ВКЛЮЧИТЬ! --------------------------------
//setInterval(createDashboard, 10000);