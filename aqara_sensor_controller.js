var host = window.location.origin;

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
function readFile() {
    function clearTable() {
        var table = document.querySelector('.sensors-table').getElementsByTagName('tbody')[0];
        table.innerHTML = '';
    }
    clearTable();

    fetch(host + '/IOT_Devices/AqaraSensor_Update')
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        var table = document.querySelector('.sensors-table');
        var tbody = document.createElement('tbody');
        tbody.classList.add('slideIn');
        var sensorValue = 0;

        for (let key in data) {
            if (key.startsWith('AqaraSensor')) {
                sensorValue++;
            }
        }

        for(let count = 1; count <= sensorValue; count++) {
            let key = 'AqaraSensor' + count;
            if (data.hasOwnProperty(key)) {
                if (key !== '') {
                    let sensorData = data[key];

                    var location = '';
                    var subLocation = '';
                    switch (count) {
                        case 1:
                        case 2:
                            location = 'ЦОД';
                            subLocation = 'Зал А';
                            break;
                        case 3:
                        case 4:
                            location = 'ЦОД';
                            subLocation = 'Зал Б';
                            break;
                        case 5:
                        case 6:
                            location = 'ЦОД';
                            subLocation = 'Зал В';
                            break;
                        case 7:
                        case 8:
                            location = 'Серверная тит. 85-01';
                            break;
                        case 9:
                        case 10:
                            location = '305-ая';
                            subLocation = 'Холодный коридор';
                            break;
                        case 11:
                        case 12:
                            location = '305-ая';
                            subLocation = 'Горячий коридор';
                            break;
                        case 13:
                        case 14:
                            location = 'ЛАЗ (Цех связи)';
                            break;
                        default:
                            location = 'Неизвестно';
                            subLocation = '';
                    }

                    table.appendChild(tbody);
                    var row = tbody.insertRow();
                    var cell1 = row.insertCell(0);
                    var cell2 = row.insertCell(1);
                    var cell3 = row.insertCell(2);
                    var cell4 = row.insertCell(3);
                    var cell5 = row.insertCell(4);
                    var cell6 = row.insertCell(5);
                    var cell7 = row.insertCell(6);
                    var cell8 = row.insertCell(7);
                    var cell9 = row.insertCell(8);
                    var cell10 = row.insertCell(9);

                    cell1.textContent = key;
                    cell2.textContent = location; /* subLocation */
                    cell3.textContent = sensorData.property_2;
                    cell4.textContent = sensorData.property_3;
                    cell5.textContent = sensorData.property_4;
                    cell6.textContent = sensorData.property_5;
                    cell7.textContent = sensorData.property_6;
                    cell8.textContent = sensorData.property_7;
                    cell9.textContent = sensorData.property_1;
                    cell10.textContent = sensorData.datetime;
                }
            }
        }
    })
    .catch(error => {
        console.error('Произошла ошибка при получении данных:', error);
    });

    function clearTable() {
        var table = document.querySelector('.sensors-table').getElementsByTagName('tbody')[0];
        table.remove();
    }
}

window.onload = readFile();