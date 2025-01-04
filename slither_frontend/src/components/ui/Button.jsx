import './Button.css'

export default function Button (props){
    return (<button onClick={props.onClick}>
        <span class="circle1"></span>
        <span class="circle2"></span>
        <span class="circle3"></span>
        <span class="circle4"></span>
        <span class="circle5"></span>
        <span class="text">{props.text}</span>
    </button>)
}