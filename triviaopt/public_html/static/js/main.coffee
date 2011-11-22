$(() ->

  current_question = null
  start_time = null
  num_right = 0
  num_wrong = 0

  loadQuestion = () ->
    $.get "/next-question", (data) ->
      console.log(data)
      comments = data[0].fields.category[0].fields.comments or ''
      current_question = data[0].pk
      question = $("""
        <table><tr>
          <td>
          <p class="category">#{data[0].fields.category[0].fields.name}</p>
          <p class="comments">#{comments}</p>
          </td>
        </tr><tr>
          <td class="question">
            <div class="inner-clue">
              #{data[0].fields.clue}
            </div>
          </td>
        </tr>
        </table>
      """)
      $("#question").html(question)
      $("#answer").val('')
      $("#answer").focus()
      start_time = new Date().getTime()

  loadQuestion()

  $("#answerform").submit (e) ->
    $.ajax("/answer-question", {
          data: {
            question_id: current_question
            answer: $("#answer").val()
          },
          success: (data) ->
            $("#answer-container").html("""
              <span class="result">#{if data.is_correct then "Correct" else "Incorrect!"}</span>
              <span class="actual-answer">#{data.correct_response}</span>
              <a href="foo" class="change-answer">(#{if data.is_correct then "Actually wrong?" else "Actually right?"})</a>
            """)
            $(".change-answer").click (e) ->
              $.ajax("/change-answer", { data: { answer_id: data.answer_id } })
              $(".change-answer").delete()
              return false
            loadQuestion()
      })
    false

)