document.addEventListener('DOMContentLoaded', function () {
    var hole = document.getElementById('hole');
    var startButton = document.getElementById('startButton');
    var stopButton = document.getElementById('stopButton');
    var dotsCounter = document.getElementById('dotsCounter');
    var totalInitialDots = document.getElementById('totalInitialDots');
    var totalCounterDots = document.getElementById('totalCounterDots');
    var totalJackPot = document.getElementById('totalJackPot');
    var totalPlayers = document.getElementById('totalPlayers');
    var gameOverMessage = document.getElementById('gameOverMessage');
    var modal = document.getElementById('participantsModal');
    var closeBtn = document.getElementsByClassName('close')[0];
    var leaderboardTable = document.getElementById('leaderboardTable');
    var Diametro = 150;
    var players = []; // Array para almacenar la información de los jugadores
    var dots = []; // Array para almacenar los puntitos
    var intervalId, gameInProgress;

    // ✅ Cargar tableros abiertos al iniciar
    obtenerTablerosAbiertos();

    // ✅ Obtener tableros abiertos
    async function obtenerTablerosAbiertos() {
        try {
            const response = await fetch('https://bolaslocas-production.up.railway.app/tableros_abiertos');
            if (!response.ok) {
                throw new Error('Error al obtener los tableros abiertos');
            }
            const tableros = await response.json();
            console.log('Respuesta del servidor:', tableros); // Depuración
            mostrarTableros(tableros);
        } catch (error) {
            console.error('Error:', error);
            alert('No se pudieron cargar los tableros abiertos.');
        }
    }

    // ✅ Mostrar tableros abiertos
    function mostrarTableros(tableros) {
        const openBoardsList = document.getElementById('open-boards-list');
        openBoardsList.innerHTML = ''; // Limpiar la lista
        if (tableros.length === 0) {
            openBoardsList.innerHTML = '<li>No hay tableros abiertos en este momento.</li>';
            return;
        }
        tableros.forEach(tablero => {
            const listItem = document.createElement('li');
            const button = document.createElement('button');
            button.innerText = `Tablero ${tablero.id_tablero} - ${tablero.nombre}`;
            button.style.padding = '10px';
            button.style.backgroundColor = '#007BFF';
            button.style.color = 'white';
            button.style.border = 'none';
            button.style.borderRadius = '5px';
            button.style.cursor = 'pointer';
            button.addEventListener('click', () => {
                obtenerJugadoresTablero(tablero.id_tablero);
            });
            listItem.appendChild(button);
            openBoardsList.appendChild(listItem);
        });
    }

    // ✅ Obtener jugadores de un tablero específico
    async function obtenerJugadoresTablero(idTablero) {
        try {
            const response = await fetch(`https://bolaslocas-production.up.railway.app/tablero/${idTablero}/jugadores`);
            if (!response.ok) {
                throw new Error('Error al obtener los jugadores del tablero');
            }
            const jugadores = await response.json();
            mostrarJugadores(jugadores);
        } catch (error) {
            console.error('Error:', error);
            alert('No se pudieron cargar los jugadores del tablero.');
        }
    }

    // ✅ Mostrar jugadores del tablero seleccionado
    function mostrarJugadores(jugadores) {
        const playersTableBody = document.querySelector('#board-players-table tbody');
        playersTableBody.innerHTML = ''; // Limpiar la tabla
        if (jugadores.length === 0) {
            playersTableBody.innerHTML = '<tr><td colspan="4">No hay jugadores en este tablero.</td></tr>';
            return;
        }
        jugadores.forEach(jugador => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${jugador.alias}</td>
                <td>${jugador.sponsor || 'N/A'}</td>
                <td>${jugador.total_bolitas}</td>
                <td style="background-color: ${jugador.color}; width: 20px; height: 20px;"></td>
            `;
            playersTableBody.appendChild(row);
        });
    }

    // ✅ Inicializar el juego
    function initializeGame() {
        clearDots(); // Borrar puntitos existentes
        dots = []; // Limpiar la matriz de puntitos
        players = [];
        gameInProgress = false;
        totalInitialDots.innerText = '0';
        totalJackPot.innerText = '0';
        totalCounterDots.innerText = '0';
        gameOverMessage.style.display = 'none';
        clearInterval(intervalId);
        hole.style.height = '150px';
        hole.style.width = '150px';
        Diametro = 150;
    }

    // ✅ Crear jugador
    function createPlayer(number, initialDots, restantes) {
        var player = {
            number: number,
            color: getRandomColor(),
            dots: [],
            initialDots: initialDots,
            restantes: restantes
        };
        players.push(player);
    }

    // ✅ Generar color aleatorio
    function getRandomColor() {
        return '#' + Math.floor(Math.random() * 16777215).toString(16);
    }

    // ✅ Crear bolita
    function createDot(player) {
        var dot = document.createElement('div');
        dot.className = 'dot';
        setRandomPosition(dot);
        dot.style.backgroundColor = player.color;
        dot.direction = Math.random() * Math.PI * 2;
        document.getElementById('game-container').appendChild(dot);
        player.dots.push(dot);
        dots.push(dot);
    }

    // ✅ Asignar posición aleatoria
    function setRandomPosition(dot) {
        dot.style.left = Math.random() * (400 - dot.offsetWidth) + 'px';
        dot.style.top = Math.random() * (400 - dot.offsetHeight) + 'px';
    }

    // ✅ Actualizar posiciones de las bolitas
    function updateDotPositions() {
        if (!gameInProgress) {
            return;
        }
        var containerWidth = 400;
        var containerHeight = 400;
        dots.forEach(function (dot, index) {
            var dotX = parseFloat(dot.style.left);
            var dotY = parseFloat(dot.style.top);
            var velocidad = 2 + (dots.length * 0.0596);
            var speed = velocidad;
            var curvature = 0.2;
            var angle = Math.random() * Math.PI * 2;
            if (dots.length === 4) {
                curvature = 0.4;
            }
            if (dots.length <= 200) {
                hole.style.height = '50px';
                hole.style.width = '50px';
                Diametro = 50;
            }
            dotX += speed * Math.cos(dot.direction);
            dotY += speed * Math.sin(dot.direction);
            dot.direction += curvature * Math.sin(angle);
            dotX = Math.max(0, Math.min(dotX, containerWidth - dot.offsetWidth));
            dotY = Math.max(0, Math.min(dotY, containerHeight - dot.offsetHeight));
            if (dotX === 0 || dotX === containerWidth - dot.offsetWidth) {
                dot.direction = Math.PI - dot.direction;
            }
            if (dotY === 0 || dotY === containerHeight - dot.offsetHeight) {
                dot.direction = -dot.direction;
            }
            var distance = Math.sqrt((dotX - 200) ** 2 + (dotY - 200) ** 2);
            if (distance < Diametro / 2) {
                removeDot(index);
            }
            if (dots.length === 1) {
                endGame();
            }
            dot.style.left = dotX + 'px';
            dot.style.top = dotY + 'px';
        });
        dotsCounter.innerText = 'Bolitas en el Tablero: ' + dots.length;
        updateLeaderboard();
    }

    // ✅ Eliminar bolita
    function removeDot(index) {
        var dot = dots[index];
        dots.splice(index, 1);
        dot.parentNode.removeChild(dot);
        totalCounterDots.innerText = parseInt(totalCounterDots.innerText) - 1;
        players.forEach(function (player) {
            var dotIndex = player.dots.indexOf(dot);
            if (dotIndex !== -1) {
                player.dots.splice(dotIndex, 1);
                player.restantes = player.restantes - 1;
                if (player.restantes > 0) {
                    createDot(player);
                }
            }
        });
    }

    // ✅ Limpiar bolitas
    function clearDots() {
        var gameContainer = document.getElementById('game-container');
        dots.forEach(function (dot) {
            if (gameContainer.contains(dot)) {
                gameContainer.removeChild(dot);
            }
        });
    }

    // ✅ Actualizar tabla de posiciones
    function updateLeaderboard() {
        players.sort(function (a, b) {
            return b.dots.length - a.dots.length;
        });
        var tableBody = document.querySelector('#leaderboardTable tbody');
        tableBody.innerHTML = '';
        for (var i = 0; i < Math.min(20, players.length); i++) {
            var row = tableBody.insertRow();
            var cell1 = row.insertCell(0);
            var cell2 = row.insertCell(1);
            var cell3 = row.insertCell(2);
            var cell4 = row.insertCell(3);
            var cell5 = row.insertCell(4);
            cell1.innerHTML = 'Jugador ' + players[i].number;
            cell2.innerHTML = players[i].dots.length;
            cell3.innerHTML = '' + players[i].color + '';
            cell4.innerHTML = players[i].initialDots;
            cell5.innerHTML = players[i].restantes;
        }
    }

    // ✅ Iniciar movimiento
    function startMovement() {
        initializeGame();
        gameInProgress = true;
        gameOverMessage.style.display = 'none';
        intervalId = setInterval(updateDotPositions, 10);
        var numPlayers = getRandomNumber(2, 50);
        totalPlayers.innerText = numPlayers;
        for (var i = 1; i <= numPlayers; i++) {
            var initialDots = getRandomNumber(10, 100);
            totalInitialDots.innerText = parseInt(totalInitialDots.innerText) + initialDots;
            var restantes = initialDots - Math.round(initialDots / 5) - 1;
            createPlayer(i, initialDots, restantes);
        }
        var JackPot = parseInt(totalInitialDots.innerText) * 400 * 0.70;
        totalJackPot.innerText = JackPot.toLocaleString("en", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
            style: "currency",
            currency: "USD"
        });
        totalCounterDots.innerText = parseInt(totalInitialDots.innerText);
        players.forEach(function (player) {
            for (var i = 0; i < Math.round(player.initialDots / 5); i++) {
                createDot(player);
            }
        });
        updateLeaderboard();
        dotsCounter.innerText = 'Bolitas en el Tablero: ' + dots.length;
    }

    // ✅ Detener movimiento
    function stopMovement() {
        gameInProgress = false;
        clearInterval(intervalId);
    }

    // ✅ Finalizar juego
    function endGame() {
        stopMovement();
        clearDots();
        gameOverMessage.style.display = 'block';
        if (players.length === 1 && players[0].dots.length === 1) {
            gameOverMessage.innerHTML = '¡Jugador ' + players[0].number + ' es el Ganador!';
        } else {
            gameOverMessage.innerHTML = 'Juego Terminado';
        }
    }

    // ✅ Mostrar participantes
    function displayParticipants() {
        var participantsTable = document.getElementById('participantsTable');
        var participantsBody = document.getElementById('participantsBody');
        participantsBody.innerHTML = '';
        players.forEach(function (player) {
            var row = participantsBody.insertRow();
            var cell1 = row.insertCell(0);
            var cell2 = row.insertCell(1);
            var cell3 = row.insertCell(2);
            var cell4 = row.insertCell(3);
            var cell5 = row.insertCell(4);
            cell1.innerHTML = 'Jugador ' + player.number;
            cell2.innerHTML = player.dots.length;
            cell3.innerHTML = '' + player.color + '';
            cell4.innerHTML = player.initialDots;
            cell5.innerHTML = player.restantes;
        });
    }

    var participantsButton = document.getElementById('participantsButton');
    participantsButton.addEventListener('click', function () {
        displayParticipants();
        modal.style.display = 'block';
    });

    closeBtn.addEventListener('click', function () {
        modal.style.display = 'none';
    });

    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    startButton.addEventListener('click', startMovement);
    stopButton.addEventListener('click', stopMovement);

    // ✅ Generar número aleatorio
    function getRandomNumber(min, max) {
        return Math.floor(Math.random() * (max - min + 1) + min);
    }
});