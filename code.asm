.data
spooked: .word 123456

.text
main:
    li $v0, 9
    li $a0, 4
    syscall
    li $t0, 10
    sw $t0, 0($v0)
    lw $t1, 0($v0)
    li $v0, 1
    move $a0, $t1
    syscall
    li $v0, 11
    li $a0, 10
    syscall
