.data
spooked: .word 123456

.text
main:
    lw $t0, spooked
    li $v0, 1
    move $a0, $t0
    syscall
    li $v0, 11
    li $a0, 10
    syscall
