<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
​
</head>
<body>
    <div id="root">
​
    </div>
    <style>
        .active {
            background-color: blueviolet;
        }
    </style>
    <script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>
    <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
    <script src="script.js" type="text/babel"></script>
</body>
</html>



'use strict';
​
function Like() {
    const [text, setText] = React.useState('')
    const [state, setState] = React.useState([])
​
​
    const addItem= () => {
        if(!text) return
        setState((s) => [...s, {id: s.length, text: text}])
        setText('')
    }
    console.log(state)
    return(<div>
        Enter text: <input type="text" value={text} onChange={(e) => setText(e.target.value)} /><br/>
        <button onClick={addItem}>Add</button>
        <ul>
        {state.map(({id, text}) => <li key={id}>{text}</li>)}
        </ul>
    </div>)
​
}
​
const domContainer = document.getElementById('root');
const root = ReactDOM.createRoot(domContainer);
root.render(React.createElement(Like));

